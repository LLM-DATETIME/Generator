# -*- coding: utf-8 -*-
"""
generate20.py: Generate a sample of dates for training

BASE
generate19.py

MODIFICATIONS
Need to generate dates like this "November 28, 2024" that appear in PeaceMonitor but are not considered as a DATE
1. added delimiter ','  (comma)

2. allow for different separators in the same string
    - in "November 28, 2024", we need both space and comma

3. implement month_schema logic created in generate18_1.py
    - month_tokens is a dict with different schemas, allowing control over the month formatting
    - default is all
    
NOTES
List of schemas available:
    - day-month-yy
    - day-month-weekday-yy
    - month-day-yy
    - month-day-weekday-yy
    - day-month-yyyy
    - day-month-weekday-yyyy
    - month-day-yyyy
    - month-day-weekday-yyyy

BACKLOG

- Single digit year 
    - e.g "01 01 01 12:01:01"

- Year in middle position 
    - e.g "Jan 2010 1st"

- Should the override that removes short strings comprised only of digits be relaxed for more generality?

USAGE
python3 generate20.py entity 10 --inputs

"""

# -------
# imports
# -------

from collections import namedtuple
from datetime import date, datetime, time, timedelta
from random import choice
from typing import Any, List, Set, Dict, Tuple, Optional, Union, Iterable, Iterator

# 3rd party
from babel.localedata import locale_identifiers
from babel import Locale

from utils.check_isinstance import check_isinstance
from utils.random_datetime import random_date
from utils.normalise_whitespace import NormaliseWhitespace
from utils.normalise_tokens import NormaliseTokens
from utils.normalise_unicode import NormaliseUnicode

from config import Config as Config
from utils.training_pair import TrainingPair
from utils.custom_formatter import CustomFormatter
from utils.normalise_tokens import NormaliseTokens as NormaliseLDMLTokens

# logging
from utils.logger import logger_dl
module_logger = logger_dl.getChild("date::generate20")

# -----
# class
# -----

class Generate:

    """
    Generate a sample of dates for training
    """

    def __init__(self, month_schema : str = "all"):
        """
        :param month_schema: specifies the month formats
            possible values:
            - "all": arabic and roman numerals
            - "arabic": arabic numerals only (1, 2, 3, ...)
            - "roman" : (i, ii, iii, ...)
            - unambiguous : MMM and MMMM
        """

        self.debug = False

        self.config = Config() # self.default_encoding_character = "?"

        # generate17: CustomFormatter
        self.custom_formatter = CustomFormatter()

        # the core datalake type being generated (see Config.core_pandas_type_map)
        self.model_name = "DATE"
        self.date_model_name = "date" # model required to process the date, currently in def_file/infer_dates/...

        # for NER (named entity resolution)
        self.entity = "date"

        # when the output (value to be predicted) is iso8601, generate the following format
        self.iso_format_date = "Y-M-d" 

        # time parts for iso8601:dt:start and iso8601:dt:end
        self.start_end_of_day = time(0, 0, 0) 
        self.time_end_of_day = time(23, 59, 59) 

        # default settings for date machine learning models
        self.date_config = Config()

         # generate17.1: iterate on all formats locales available in Babel; currently 789 locales in Babel
        self.all_locales = locale_identifiers() # all locales in Babel

        if self.debug:
            module_logger.debug(f"#locales available in Babel : {len(self.all_locales)}")

        self.locale_schemas = { 
            "en_US" : ["en_US"]
            , "mini.10" : self.config.mini10_locales # hand-curated list of 10 locales
            , "sap.dominant" :self.config.sap_dominant_locales # hand-curated by SAP, Babel compatible
            , "babel.all" : list(locale_identifiers()) # all locales available in Babel
            , "all" : list(locale_identifiers()) # all locales available in Babel
            }
        
        # normalisation

        # replace {whitespace} tokens in the formats below with this character
        # important: we don't want to use a space as a whitespace character, because then we cannot parse tokens correctly
        # e.g 01:12:31 da tarde 
        # the above string is not trivual to parse using space as a delimiter, because da tarde belongs together as a single token
        # thus we use a token such as ? to facilitate the parsing
        # -> 01:12:31?a tarde 
        self.whitespace_character = ' ' 

        # NB: the 4 default format specs (short, medium, long and full) do not provide additional span of the format space
        # leading to overfitting; thus additional formats are added manually in the constructor

        # {whitespace} token is replaced with the values from whitespace_characters
        # BACKLOG: the 'at' does not get localised
        
        # generate15.py | added "no separator" to generate dates with no spaces between tokens, e.g 111212
        #self.separators = [' ', '.', '/', '-', '#', '|', '']
        # generate17.py: removed no separator, it's too aggressive and generates really tough pairs
        self.separators = [' ', '.', '/', '-', '#', '|', ',']

        # generate12.py: list of tokens used for the patterns
        # generate17.py: added patterns from CustomFormatter
        # {C(day)}        one
        # {O(day)}        first
        # {ON(day)}       1st
        # {X(month)}      IV
        # {X(year)}       MMVII
        self.day_tokens = [ r"{d}", r"{dd}", r"{C(day)}", r"{O(day)}", r"{ON(day)}" ]

        # month tokens
        # generate18_1: month_tokens is a dict with different schemas, allowing control over the month formatting
        self.all_month_tokens = {
            "all" : [ r"{M}", r"{MM}", r"{MMM}", r"{MMMM}", r"{X(month)}" ]
            , "arabic" : [ r"{M}", r"{MM}", r"{MMM}", r"{MMMM}"]
            , "unambiguous" : [ r"{MMM}", r"{MMMM}"]
            , "roman" : [ r"{X(month)}" ]
        }

        # generate18_1: month_tokens is a dict with different schemas, allowing control over the month formatting
        self.set_month_schema(month_schema)

        # BACKLOG: year in romand numerals r"{X(year)}"
        # NOTE! don't forget to keep generate16.12 in sync with tokens that have century
        self.year_tokens = [ r"{yy}", r"{yyyy}" ] 

        # DOC: https://babel.pocoo.org/en/latest/dates.html#date-fields
        self.format_spec = { 
            
                            # schema day-month: day represented before month
                            "day-month-yy" : [  

                                # day, month, year
                                # 1 digit day
                                r"{day}{separator}{month}{separator}{yy}" 

                                # year, day, month
                                # 1 digit day
                                , r"{yy}{separator}{day}{separator}{month}" 


                            ]
                            
                            , "day-month-weekday-yy" : [  

                                # day of week, day, month, year
                                # E: Day of week. Use one through three letters for the short day, or four for the full name, or five for the narrow name.
                                # doc: https://babel.pocoo.org/en/latest/dates.html#date-fields
                                r"{E}{whitespace}{day}{separator}{month}{separator}{yy}"
                                , r"{EE}{whitespace}{day}{separator}{month}{separator}{yy}"
                                , r"{EEE}{whitespace}{day}{separator}{month}{separator}{yy}"
                                , r"{EEEE}{whitespace}{day}{separator}{month}{separator}{yy}"   # vrijdag 19 jan. 1990

                            ]
                            
                            # schema month-day: month represented before day
                            , "month-day-yy" : [

                                # month, day, year
                                # 1 digit day
                                r"{month}{separator}{day}{separator}{yy}" 

                                 # year, month, day
                                # 1 digit day
                                , r"{yy}{separator}{month}{separator}{day}" 


                            ]

                            , "month-day-weekday-yy" : [

                                # day of week, e.g Friday 19 Jun 2011
                                # day of week, day, month, year
                                # E: Day of week. Use one through three letters for the short day, or four for the full name, or five for the narrow name.
                                # doc: https://babel.pocoo.org/en/latest/dates.html#date-fields
                                r"{E}{whitespace}{month}{separator}{day}{separator}{yy}"
                                , r"{EE}{whitespace}{month}{separator}{day}{separator}{yy}"
                                , r"{EEE}{whitespace}{month}{separator}{day}{separator}{yy}"
                                , r"{EEEE}{whitespace}{month}{separator}{day}{separator}{yy}"

                                , r"{month}{separator}{E}{whitespace}{day}{separator}{yy}"
                                , r"{month}{separator}{EE}{whitespace}{day}{separator}{yy}"
                                , r"{month}{separator}{EEE}{whitespace}{day}{separator}{yy}"
                                , r"{month}{separator}{EEEE}{whitespace}{day}{separator}{yy}"

                            ]

                            # schema day-month: day represented before month
                            , "day-month-yyyy" : [  

                                # day, month, year
                                # 1 digit day
                                r"{day}{separator}{month}{separator}{yyyy}" 

                                # year, day, month
                                # 1 digit day
                                , r"{yyyy}{separator}{day}{separator}{month}" 


                            ]
                            
                            , "day-month-weekday-yyyy" : [  

                                # day of week, day, month, year
                                # E: Day of week. Use one through three letters for the short day, or four for the full name, or five for the narrow name.
                                # doc: https://babel.pocoo.org/en/latest/dates.html#date-fields
                                r"{E}{whitespace}{day}{separator}{month}{separator}{yyyy}"
                                , r"{EE}{whitespace}{day}{separator}{month}{separator}{yyyy}"
                                , r"{EEE}{whitespace}{day}{separator}{month}{separator}{yyyy}"
                                , r"{EEEE}{whitespace}{day}{separator}{month}{separator}{yyyy}"   # vrijdag 19 jan. 1990

                            ]
                            
                            # schema month-day: month represented before day
                            , "month-day-yyyy" : [

                                # month, day, year
                                # 1 digit day
                                r"{month}{separator}{day}{separator}{yyyy}" 

                                 # year, month, day
                                # 1 digit day
                                , r"{yyyy}{separator}{month}{separator}{day}" 


                            ]

                            , "month-day-weekday-yyyy" : [

                                # day of week, e.g Friday 19 Jun 2011
                                # day of week, day, month, year
                                # E: Day of week. Use one through three letters for the short day, or four for the full name, or five for the narrow name.
                                # doc: https://babel.pocoo.org/en/latest/dates.html#date-fields
                                r"{E}{whitespace}{month}{separator}{day}{separator}{yyyy}"
                                , r"{EE}{whitespace}{month}{separator}{day}{separator}{yyyy}"
                                , r"{EEE}{whitespace}{month}{separator}{day}{separator}{yyyy}"
                                , r"{EEEE}{whitespace}{month}{separator}{day}{separator}{yyyy}"

                                , r"{month}{separator}{E}{whitespace}{day}{separator}{yyyy}"
                                , r"{month}{separator}{EE}{whitespace}{day}{separator}{yyyy}"
                                , r"{month}{separator}{EEE}{whitespace}{day}{separator}{yyyy}"
                                , r"{month}{separator}{EEEE}{whitespace}{day}{separator}{yyyy}"

                            ]



                        } # self.format_spec


        self.all_schemas = list(self.format_spec.keys())

        self.possible_components = {
            "year" : self.year_tokens
            , "month" : self.month_tokens
            , "day" : self.day_tokens
        }


    def set_month_schema(self, month_schema : str):
        """
        :param month_schema: specifies the month formats
            possible values:
            - "all": arabic and roman numerals
            - "arabic": arabic numerals only (1, 2, 3, ...)
            - "roman" : (i, ii, iii, ...)
            - unambiguous : MMM and MMMM
        """
        
        if month_schema not in self.all_month_tokens:
            raise ValueError(f"month schema {month_schema} not found")
        
        self.month_tokens = self.all_month_tokens[month_schema]
        self.month_schema = month_schema

        if self.debug:
            module_logger.debug(f"month_schema : {month_schema} | tokens : {self.month_tokens}")

    def resolve_dmy_tokens(self, raw_format_spec : str) -> str:

        """
        resolve_dmy_tokens: replace a string with generic tokens "{day} {month} {year}" to a string with implementable tokens
            e.g "{dd} {MMM} {YYYY}"

        
        :param faw_format_spec: a string with generic tokens, e.g "{day} {month} {year}" 

        :return: a string with implementable tokens, e.g "{dd} {MMM} {YYYY}"
        
        """

        # generate17: resolve {day}, {month} and {year} tokens
        assert r"{day}" in raw_format_spec
        assert r"{month}" in raw_format_spec
        

        day_token = choice(self.day_tokens)
        month_token = choice(self.month_tokens)
        

        raw_format_spec = raw_format_spec.replace(r"{day}", day_token)
        raw_format_spec = raw_format_spec.replace(r"{month}", month_token)

        # generate18: {year} no long present in the formats, but we can generalise the code
        if r"{year}" in raw_format_spec:
            year_token = choice(self.year_tokens)
            raw_format_spec = raw_format_spec.replace(r"{year}", year_token)

        return raw_format_spec

    def _get_loc(self, format_spec : str, get_format_spec : str, dt : datetime, locale : str) -> Tuple[List[int], str]:

        """

        NOTE: copied from dates/datetime/generate16.22.py

        _get_loc: return the index locations of get_format_spec
            example, return the index locations where {dd} appears in the string
            NOTE: returns a sparse location, not one-hot-encoded => [4,5,6]

        :param format_spec: the full format spec of the datetime, with all components
            e.g. {EEE} {dd} {MMMM} {yyyy} ,{h}:{m}:{ss} {a}


        :param get_format_spec: format of which the location must be extracted
            e.g "{MMMM}", "X(month)", ...

        :param dt: datetime on which to operate

        :param locale: locale for text generation


        :return: 2-tuple;
            1. list of integers with the index position of get_format_spec 
                can be used for multi-label classification (lstm_seq2multi_label_batch expects integers only)
                e.g [4, 5, 6, 7]

            2. the value of the component specified in get_format_spec
                e.g "nov"

        
        """

        
        # let's first check that the format to be extracted actually exists in the format spec
        assert get_format_spec in format_spec

        # add special character to delimit the month, so we can then carve out the month as represented by the current format
        # check the special character does not already exist
        etx = "!" # chr(3) 
        assert etx not in format_spec

        date_format_spec_1 = format_spec.replace(get_format_spec, etx + get_format_spec + etx)
        #print(f"format_spec : {format_spec}")
        #print(f"input_str : {input_str}")
        #print(f"date_format_spec_1 : {date_format_spec_1}")

        # generate 16.12: apply custom formats + Babel
        output_str_1 = self.custom_formatter.apply(date_format_spec_1, dt, locale=locale)
        #print(f"output_str_1 : {output_str_1}")

        # split on ETX character
        loc_start = output_str_1.find(etx)
        assert loc_start != -1

        # find last ETX character
        loc_end = output_str_1.find(etx, loc_start+1)
        assert loc_end != -1
        assert loc_end >= loc_start
        
        # check no more ETX characters
        assert output_str_1.find(etx, loc_end+1) == -1

        # remove the two special characters that were inserted
        loc_end -= 2 

        # test it worked using a round trip
        # carve out string between loc_start andloc_end
        input_str = self.custom_formatter.apply(format_spec, dt, locale=locale)
        
        # NOTE: test string must also be normalised for comparison with the target string, e.g remove trailing spaces
        #test_target = input_str[loc_start:(loc_end+1)]
        test_target = self.custom_formatter.normalise_string(input_str[loc_start:(loc_end+1)])
        
        #print(f"test_target : {test_target}")

        #  check our carve out is equal to the rendered string for this format only
        # generate 16.12: apply custom formats + Babel
        output_str_2 = self.custom_formatter.apply(get_format_spec, dt, locale=locale)
        #print(f"output_str_2 : {output_str_2}")

        if test_target != output_str_2:
            raise ValueError(f"getloc | expected {test_target} | found {output_str_2} | input_str : {input_str} | format_spec : {format_spec} | locale : {locale}")

        if self.debug:
            module_logger.debug(f"getloc | get_format_spec : {get_format_spec} | loc : [{loc_start}:{loc_end}] | extracted : '{test_target}' | expected : '{output_str_2}'")

        # create multi-label output list
        # NOTE: lstm_seq2multi_label_batch expects integers only
        return [i for i in range(loc_start, loc_end+1)], output_str_2 # REM: ub not inclusive 

    
    def get_visible_components(self, format_spec : str) -> Dict:
        """

        Get the components that are visible in the output string. 

        For example, the input datetime may have microseconds, but if they are not in the output string

        :param format_spec: the format of the datetime; 
            format_spec: {h}:{mm}:{s} {a} {ZZ} {MMMM}#{EEEE} {ON(day)}#{yyyy}



        :return: a dict with visible components and the format 
            e.g 
            {   "year" : "{yyyy}"
                ,  "month" : "{MM}"
                , ...
                , "timezone" : "{z}"
                }
        
        
        """

        visible_components = {}

        for possible_component, possible_component_formats in self.possible_components.items():
            for possible_component_format in possible_component_formats:
                if possible_component_format in format_spec:
                    if possible_component not in visible_components:
                        visible_components[possible_component] = possible_component_format
                    else:
                        raise RuntimeError(f"Found the component {possible_component} more than once in the format {format_spec}. Token is '{possible_component_format}'.")

        return visible_components
    
    def _day_month_order(self, raw_format_spec : str) -> str:
        """
        Parse the token string and determien if the day appears before the month, or vice-versa ("day-month-order")

        :param raw_format_spec1: a format string that contains the tokens {day}, {month} and {yy} (and possibly other tokens)
            e.g  r"{month}{separator}{day}{separator}{yyyy}" 

        :return: either "day-month" or "month-day"
        
        """
        
        check_isinstance(raw_format_spec, str)

        # check the raw_format_spec1 contains the tokens {day}, {month} and {yy} (and possibly other tokens for whitespace, separators, etc)
        assert r"{day}" in raw_format_spec
        assert r"{month}" in raw_format_spec

        day_loc = raw_format_spec.find(r"{day}")
        month_loc = raw_format_spec.find(r"{month}")
        assert day_loc != -1
        assert month_loc != -1
        assert day_loc != month_loc

        return "day-month" if day_loc < month_loc else "month-day"


    def _get_spans(self, input_str : str, format_spec : str, dt : datetime, locale : str) -> List[str]:
        """

        :param format_spec: the format of the date; 

        :param dt: datetime on which to operate

        :param locale: locale for text generation


        """

        """
        get_visible_components returns a dict with visible components and the format 
            e.g 
            {   "year" : "{yyyy}"
                ,  "month" : "{MM}"
                , ...
                , "timezone" : "{z}"
                }
        """

        #print(f"input_str : {input_str}")
        #print(f"format_spec : {format_spec}")
        #print(f"dt : {dt}")
        #print(f"locale : {locale}")
        
        visible_components = self.get_visible_components(format_spec)
        #print(f"visible_components : {visible_components}")

        # start by creating an empty list with NULL locations at each index
        spans = ["NULL"] * len(input_str)

        # for each visible component
        for visible_component_name, visible_component_format in visible_components.items():
            
            # _get_loc -> Tuple[List[int], str]
            """
            _get_loc returns a 2-tuple
            1. list of integers with the index position of get_format_spec 
                can be used for multi-label classification (lstm_seq2multi_label_batch expects integers only)
                e.g [4, 5, 6, 7]

            2. the value of the component specified in get_format_spec
                e.g "nov"
            """
            visible_component_loc, visible_component_value = self._get_loc(format_spec, visible_component_format, dt, locale)

            #print(f"visible_component_loc : {visible_component_loc}")
            #print(f"visible_component_value : {visible_component_value}")

            for idx in visible_component_loc:
                spans[idx] = visible_component_name

            #print(f"spans : {spans}")
            
        return spans
    
    def generate(self
                , output : str
                , num_observations : int
                , start_date : datetime = None
                , schemas : List[str] = None
                , locale_schema : str = None
                ) -> Iterator[ Tuple[ TrainingPair, datetime] ]:

        """

        :param output: what do generate: iso8601, pattern

        :param num_observations: number of dates to generate; each date will be generated in N(locales) and N(format_spec)

        :param start_date: optional; start date(time) of the dates; a default value will be generated if None

        :param schemas: optional; list schemas to be used; at the moment only month-day and day-month are supported
            a schema is a group of formats, grouped according to some logic, e.g day first, month first, etc
            if None, all available schemas are used

            examples
            ["day-month-yy", "day-month-weekday-yy", "day-month-yyyy", "day-month-weekday-yyyy"]

        :return: function is a generator -> an iterator of 2-tuples
            1. TrainingPairs (namedtuple)
            2. the input date

        """

        assert isinstance(output, str)
        
        # set start date
        # NOTE: datetime with no tzinfo in the constructor, datetime assumes the local timezone of the computer
        # in turn, Babel interprets this as the local timezone of the locale
        # thus, with the current code logic (no tzinfo in the constructor), each locale show's it's own timezone
        if start_date is None:
            start_date = datetime(1990, 1, 1, 0, 0, 0)

        d = start_date

        # generate11: resolve schemas to be used
        # by default, use all schemas available
        if schemas is not None:
            assert type(schemas) is list

            final_schemas = []

            # check we know this schema
            for schema in schemas:
                # NOTE: simply ignore it if we can't handle it
                #assert schema in self.format_spec
                if schema in self.format_spec:
                    final_schemas.append(schema)
                else:
                    module_logger.warning(f"Ignored unhandled schema '{schema}'")
        
            schemas = final_schemas

            if self.debug:
                module_logger.debug(f"Schemas specified as arguments | using {len(schemas)} schemas | {schemas}")
        else:
            schemas = self.all_schemas

            if self.debug:
                module_logger.debug(f"No schemas specified | using all {len(schemas)} schemas | {schemas}")
        
        if len(schemas) == 0:
            raise RuntimeError(f"no schemas supported")

        # generate12: resolve locales to be used
        locale_schema_name = "all"
        
        if locale_schema is not None:
            if locale_schema not in self.locale_schemas:
                raise RuntimeError(f"locale_schema '{locale_schema}' not found in {self.locale_schemas.keys()}")
            locale_schema_name = locale_schema

        locales = self.locale_schemas[locale_schema_name]

        if self.debug:
            module_logger.debug(f"using locale schema '{locale_schema_name}' with {len(locales)} locales")

        # built-in formats
        idx = 0
        # NOTE: generate19: use a while loop to generate observation because we may have to skip certain pairs (see continue statements)
        #for idx in range(0, num_observations):
        while idx < num_observations:
            
            # generate16: generate a random date in the range [start_date; ...] with UTC timezone
            d = random_date(start_date)
         
            # generate11: iterate on requested schemas

            # generate16: randomised output
            schema = choice(schemas)
            locale = choice(locales)
                
            # iterate on date formats in this schema
            # raw_format_spec1 contains the tokens {day}, {month} and {yy} (and possibly other tokens for whitespace, separators, etc)
            raw_format_spec1 = choice(self.format_spec[schema])

            # generate17: resolve {day}, {month} and {year} tokens
            raw_format_spec = self.resolve_dmy_tokens(raw_format_spec1)

            # replace {whitespace} token with some token
            format_spec = raw_format_spec.replace(r"{whitespace}", self.whitespace_character)
            
            # replace {separator} token with some token
            # generate20: allow for different separators in the same date string
            while r"{separator}" in format_spec:
                # choose a different separator for each instance
                _separator_character = choice(self.separators)
                # NOTE: The third parameter is the maximum number of occurrences that you want to replace => replace one at a time
                format_spec = format_spec.replace(r"{separator}", _separator_character, 1)


            # generate 17: apply custom formatting 
            # NOTE: custom_formatter also applies Babel formatting
            # NOTE: generate 19: custom_formatter also applies full normalisation
            # => apply full normalisation
            # 1. unicode
            # 2. tokens (e.g convert .. to .)
            # 3. whitespace (e.g "\u202f" to " ")
            # 4. convert to lower case
            input_str = self.custom_formatter.apply(format_spec, d, locale=locale)
        

            # NOTE: presently, generate18 does not remove random components from the string
            # for compatibility with future versions of the code, we place the flags here
            component_removed = None
            removed_component = None

            # Override: remove short dates comprised only of digits, such as "12121"; this is really too tough at the moment
            # BACKLOG: should this override be relaxed for more generality?
            if len(input_str) < 6 and input_str.isdigit():
                #module_logger.warn(f"ignorning output string '{input_str}' generated from '{format_spec}")
                continue

            # -- different outputs can be specified --

            # NOTE: optional output can be added to the TrainingPair; default is None
            aux_info = None

            # for NER (named entity resolution)
            if output == "entity": 
                output_str = self.entity

            elif output == "visible_components":
                output_str = self.get_visible_components(format_spec)

            elif output == "day-month-order":
                output_str = self._day_month_order(raw_format_spec1)

            elif output == "spans":
                """
                spans: produce a single list with the locations of the components, encoded
                """

                # BACKLOG: some output generate errors
                try:
                    output_str = self._get_spans(input_str, format_spec=format_spec, dt=d, locale=locale)
                except Exception as e:
                    continue

            elif output == "format": 
                output_str = raw_format_spec

            elif output == "raw_format_spec": 
                output_str = raw_format_spec

            elif output == "format_spec": 
                output_str = format_spec

            # generate11
            elif output == "schema": 
                output_str = schema

            elif output == "year":
                output_str = str(d.year)

            elif output == "year_loc":

                # year_loc: location of the year; returns a list of indices of the year in the string

                # determine which year spec is currently used for the year; and check the year spec only appears once in the format string
                # NOTE: we must check if the year is present because it may have been randomly removed in remove_random_component()
                year_format_spec = None

                # generate16.12: we can use the exact list specified in the date model
                for _year_format in self.year_tokens:

                    if _year_format in format_spec:
                        assert year_format_spec is None # check no duplicates
                        year_format_spec = _year_format

                
                year_removed = False
                if year_format_spec is None:
                    # oups: could not find the a year... maybe we removed it above?
                    if component_removed is not None and removed_component in self.year_tokens:
                        # there is no year since it was removed
                        # generate16.20: handle missing components by generating NULL/empty bit vectors
                        year_removed = True
                    else:
                        # this is a bug
                        raise RuntimeError(f"no year token found in format_spec {format_spec}")

                # year_loc: location of the year as a list of integers
                # BACKLOG: handle cases where year was removed randomly
                assert year_removed is not True
                output_str, year_str = self._get_loc(format_spec, year_format_spec, d, locale)

                # add aux data to the training pair, for round trip
                aux_info = { "component" : "year", "str" : year_str, "value" : d.year }

            elif output == "month":
                """
                - 'fredag januar.19.1990' -> output='1'
                - 'enero 19 90' -> output='1'
                - '1.19.1990' -> output='1'
                """
                output_str = str(d.month)

            elif output == "month_loc":

                # month_loc: location of the month; returns a list of indices of the month in the string

                # determine which month spec is currently used for the month; and check the month spec only appears once in the format string
                # NOTE: we must check if the month is present because it may have been randomly removed in remove_random_component()
                month_format_spec = None

                # generate16.12: we can use the exact list specified in the date model
                for _month_format in self.month_tokens:

                    if _month_format in format_spec:
                        assert month_format_spec is None # check no duplicates
                        month_format_spec = _month_format

                
                month_removed = False
                if month_format_spec is None:
                    # oups: could not find the a month... maybe we removed it above?
                    if component_removed is not None and removed_component in self.month_tokens:
                        # there is no month since it was removed
                        # generate16.20: handle missing components by generating NULL/empty bit vectors
                        month_removed = True
                    else:
                        raise RuntimeError(f"no month token found in format_spec {format_spec}")
                    
                # BACKLOG: handle cases where month was removed randomly
                assert month_removed is not True
                
                # month_loc: location of the month as a list of integers
                output_str, month_str = self._get_loc(format_spec, month_format_spec, d, locale)

                # add aux data to the training pair, for round trip
                aux_info = { "component" : "month", "str" : month_str, "value" : d.month }
            
            elif output == "day":
                output_str = str(d.day)
            
        
            elif output == "day_loc":

                # day_loc: location of the day; returns a list of indices of the day in the string

                # extract the day, in some shape or form
                # in common, these formats require getting the day format in the format spec

                # determine which day spec is currently used for the day; and check the day spec only appears once in the format string
                # NOTE: we must check if the day is present because it may have been randomly removed in remove_random_component()
                day_format_spec = None

                # generate16.12: we can use the exact list specified in the date model
                for _day_format in self.day_tokens:

                    if _day_format in format_spec:
                        assert day_format_spec is None # check no duplicates
                        day_format_spec = _day_format

                day_removed = False
                if day_format_spec is None:
                    # oups: could not find the a day... maybe we removed it above?
                    if component_removed is not None and removed_component in self.day_tokens:
                        # there is no day since it was removed => skip this pair
                        day_removed = True
                    else:
                        raise RuntimeError(f"no day token found in format_spec {format_spec}")
                    
                # BACKLOG: handle cases where day was removed randomly
                assert day_removed is not True
                
                # NOTE: some locales generate errors when extracting the day
                # getloc | expected | | found  | input_str : |09|07 | format_spec : {EEEE} {O(day)}|{MM}|{yy} | locale : ko_KR
                try:
                    output_str, day_str = self._get_loc(format_spec, day_format_spec, d, locale)

                    # add aux data to the training pair, for round trip
                    aux_info = { "component" : "day", "str" : day_str, "value" : d.day }
                except Exception as e:
                    if self.debug:
                        module_logger.warning(f"error in day_loc : {e}")

                    continue

            elif output == "day.month.order":
                # day.month.order: the ordering of the day and month; 3 possible values:
                # 1. NULL: ambiguous: impossible to say what the order is (without exogenous knowledge)
                # 2. day-month
                # 3. month-day
                if r"{MMM}" in raw_format_spec or r"{MMMM}" in raw_format_spec or d.day > 12:
                    # un-ambiguous case 
                    # determine the ordering 1 or 2
                    output_str = schema
                else:
                    # ambiguous case 
                    output_str = "NULL"


            # generate 11: alternative model, where possible
            # month.alt: month is day
            # day.alt: day is month
            elif output == "day.alt": # alternative hypothesis
                
                # day can be the month ONLY IF month is not in text format
                # only if month is in numerical format
                # d.day == d.month: there is no ambiguity if day and month are the same
                if r"{MMM}" in raw_format_spec or r"{MMMM}" in raw_format_spec or d.day == d.month:
                    output_str = self.ml_config.null_target
                else:
                    output_str = str(d.month)
                
            elif output == "day.2":
                # day.2: output is either the single day number or a pipe | separated string with possible day numbers
                # e.g 1
                # or 1|2

                if r"{MMM}" in raw_format_spec or r"{MMMM}" in raw_format_spec or d.day == d.month or d.day > 12:
                    # unambiguous case: there is only one day possible
                    output_str = str(d.day)
                else:
                    # ambiguous case -> show all possibilities
                    # reduce target cardinality by showing smallest first (ie. reduce 2|1 to 1|2)
                    
                    # also input string '01 02 1990' always needs to have the same output '1|2'
                    # and not '1|2' or '2|1'
                    if d.day < d.month:
                        output_str = f"{d.day}|{d.month}"
                    else:
                        output_str = f"{d.month}|{d.day}"

            elif output == "month.2":
                # month.2: output is either the single month number or a pipe | separated string with possible month numbers
                # e.g 1
                # or 1|2

                # month can be the day ONLY IF day <= 12 and month is NOT in numerical format
                # d.day == d.month: there is no ambiguity if day and month are the same
                if d.day <= 12 and r"{MMM}" not in raw_format_spec and r"{MMMM}" not in raw_format_spec and d.day != d.month:
                    # ambiguous case -> show all possibilities
                    # reduce target cardinality by showing smallest first (ie. reduce 2|1 to 1|2)
                    
                    # also input string '01 02 1990' always needs to have the same output '1|2'
                    # and not '1|2' or '2|1'
                    if d.day < d.month:
                        output_str = f"{d.day}|{d.month}"
                    else:
                        output_str = f"{d.month}|{d.day}"
                else:
                    output_str = str(d.month)

            elif output == "month.alt":
                # month can be the day ONLY IF day <= 12 and month is NOT in numerical format
                # d.day == d.month: there is no ambiguity if day and month are the same
                if d.day <= 12 and r"{MMM}" not in raw_format_spec and r"{MMMM}" not in raw_format_spec:
                        output_str = str(d.day)
                else:
                    output_str = self.ml_config.null_target

            elif output == "locale": 
                output_str = locale

            elif output == "date_format": 
                output_str = format_spec

            elif output == "type":
                # predict the core datalake types, defined in datalake/config.py
                # DATE, DATETIME, STR, INT, FLOAT, BOOL, LONG
                output_str = "DATE"
                                            
            elif output == "iso8601":
                output_str = format_date(d, locale=locale, format=self.iso_format_date)

            elif output == "iso8601:dt:start":
                output_str = datetime.combine(d, self.start_end_of_day).isoformat()

            elif output == "iso8601:dt:end":
                output_str = datetime.combine(d, self.time_end_of_day).isoformat()

            elif output == "parsestr":
                output_str = format_spec

        
            elif output == "model": # used by train_meta.py

                # important: do not normalise the input string when predicting the model
                # this is because when use the meta OVR models, we are using the raw strings to predict types
                # however, when predicting the parsing string (e.g normparsestr), then we already know that the type is a date
                # so we can then normalise 
                output_str = self.model_name # e.g DATE; use in train_meta.py to predict the datatype (INT, FLOAT, DATE, etc)

            elif output == "date_model": # used by train_meta.py
                output_str = self.date_model_name

            else:
                raise RuntimeError(f"unhandled output '{output}'")
            

            if self.debug:
                print(f"{idx} / {num_observations} | {d} | {locale} | {format_spec} | {input_str} | {output_str}")

            
            #print(f"{d} | {schema} | {input_str} | {output_str}")
            
            idx += 1
            yield (TrainingPair(input_str, output_str, locale, aux_info), d)
            

                        

            # as we have memory limitations and cannot load a too large training set into the NN
            # we need a way to span a large span of dates in limited rows
            # idea is to increment the datetime with a step that is out-of-phase with time and thus generates
            # high cardinality

            # outupt example
            # TrainingPair(input='1/1/90 12:00 AM', output='{M}/{d}/{yy} {h}:{mm} {a}')
            # TrainingPair(input='11, mai., 2040, 7:58:11, da tarde', output='{d}, {MMM}, {y}, {h}:{mm}:{ss}, {a}')

            # generate11: modified timedelta
            #d += timedelta(days=1)





# -----
# main
# -----

if __name__ == "__main__":

    def main():

        from argparse import ArgumentParser

        # --- command line args ---
        cmd_line_parser = ArgumentParser(description='driver for Generate')
        cmd_line_parser.add_argument('output', type=str, default=None, help='iso8601, parsestr, model')
        cmd_line_parser.add_argument('num_observations', type=int, default=None, help='number of observations to generate')

        cmd_line_parser.add_argument('--start_date', type=str, help='start datetime, in ISO861 format', default=None)
        cmd_line_parser.add_argument('--locale_schema', type=str, help='locale schame', default="mini.10")
        cmd_line_parser.add_argument('--schemas', type=str, help='comma separated list if schemas to use', default=None)

        cmd_line_parser.add_argument('--inputs', default=False, dest='inputs', action='store_true', help='show inputs only')
        cmd_line_parser.add_argument('--outputs', default=False, dest='outputs', action='store_true', help='show outputs (targets) only')
        
        cmd_line_parser.add_argument('--debug', default=False, dest='debug', action='store_true', help='debugging')
        args = cmd_line_parser.parse_args()

        # create generator
        generator = Generate()
        generator.debug = args.debug

        # optional: specify start_date
        start_date = datetime.fromisoformat(args.start_date) if args.start_date is not None else None
        module_logger.debug(f"start_date : {start_date}")

        # optional: specify schema(s)
        schemas = None
        if args.schemas is not None:
            schemas = [schema.strip() for schema in args.schemas.split(",")]
            module_logger.debug(f"schemas : {schemas}")

        results = generator.generate(args.output
                                , args.num_observations
                                , start_date=start_date
                                , schemas=schemas
                                , locale_schema=args.locale_schema
                                )

        # show output
        for idx, (training_pair, _) in enumerate(results, start=1):
            if not args.inputs and not args.outputs:
                print(training_pair.output, "->", training_pair.input)
            elif args.inputs:
                print(training_pair.input)
            elif args.outputs:
                print(training_pair.output)

    main()    