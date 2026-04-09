# -*- coding: utf-8 -*-
"""
generate15.py: Generate a sample of times for training

base: generate14.py

MODIFICATIONS:
1. Implement six schemas to improve the control over the time formats
    - hours
    - hours-minutes
    - hours-minutes-seconds
    - hours-minutes-seconds-microseconds
    - hours-minutes-seconds-microseconds-timezone
    - hours-minutes-seconds-timezone

BACKLOG

USAGE
python3 generate15.py iso8601 10
python3 generate15.py iso8601 1000 --inputs

python3 generate15.py iso8601 10 --schemas "hours, hours-minutes, hours-minutes-seconds" --inputs

"""

# -------
# imports
# -------

from collections import namedtuple
from datetime import date, datetime, time, timedelta
from random import choice
from typing import Any, List, Set, Dict, Tuple, Optional, Union, Iterable, Iterator

# 3rd party
from babel.dates import format_time
from pytz import timezone, all_timezones

from utils.random_datetime import random_utc_datetime
from utils.custom_formatter import CustomFormatter
from utils.normalise_whitespace import NormaliseWhitespace
from utils.normalise_tokens import NormaliseTokens
from utils.normalise_tokens import NormaliseTokens as NormaliseLDMLTokens
from utils.normalise_unicode import NormaliseUnicode

from utils.training_pair import TrainingPair
from config import Config as DateConfig

# logging
from utils.logger import logger_dl
module_logger = logger_dl.getChild("time::generate15")

# -----
# class
# -----

class Generate:

    """
    Generate a sample of dates for training
    """

    def __init__(self):

        self.name = "generate15"

        self.debug = False

        # the core datalake type being generated (see Config.core_pandas_type_map)
        self.model_name = "TIME"

        # for NER (named entity resolution)
        self.entity = "time"

        # when the output (value to be predicted) is iso8601, generate the following format
        # H: Hour [0-23].
        # see http://babel.pocoo.org/en/latest/dates.html#time-fields
        self.iso_format_date = "H:m:s" 

        # default settings for date machine learning models
        self.date_config = DateConfig()

        self.locales = self.date_config.locales

        # generate14: CustomFormatter
        self.custom_formatter = CustomFormatter()
        
        
        # important: we don't want to use a space as a whitespace character, because then we cannot parse tokens correctly
        # e.g 01:12:31 da tarde 
        # the above string is not trivual to parse using space as a delimiter, because da tarde belongs together as a single token
        # thus we use a token such as ? to facilitate the parsing
        # -> 01:12:31?a tarde 
        self.whitespace_character = ' '

        self.normalise_tokens = NormaliseTokens()
        self.normalise_ldml_tokens = NormaliseLDMLTokens()
        self.normalise_whitespace = NormaliseWhitespace()
        self.normalise_unicode = NormaliseUnicode()

        # generate10.py: Added "no separator" to generate datetimes with no spaces between tokens, e.g 111212
        # generate14: I think no space between time elements hour, minute and second is really too aggressive...
        #self.separators = [ ':', ' ', '' ]
        self.separators = [ ':' ]

        # generate12.py: microsecond formats
        # generate14.py: add curly braces to microsecond foramts for consistency with other generators
        self.microsecond_formats = [ r"{S}", r"{SS}", r"{SSS}", r"{SSSS}", r"{SSSSS}", r"{SSSSSS}"]

        # generate14.py: timezone formats to iterate on
        # doc: https://babel.pocoo.org/en/latest/dates.html#time-fields
        # src:  babel/dates.py/format_timezone at line 1435

        # NOTES
        self.timezone_formats = [r"{z}", r"{zz}", r"{zzz}", r"{zzzz}"
                                , r"{Z}", r"{ZZ}" , r"{ZZZ}", r"{ZZZZ}", r"{ZZZZZ}"
                                
                                , r"{OOOO}"
                                , r"{v}",  r"{vvvv}"
                                , r"{V}",  r"{VV}", r"{VVV}", r"{VVVV}"
                                , r"{X}",  r"{XX}", r"{XXX}", r"{XXXX}", r"{XXXXX}"
                                , r"{x}",  r"{xx}", r"{xxx}", r"{xxxx}", r"{xxxxx}"
                                , r"{T}", r"{TT}"
                                ]

        self.time_modifier_formats = [ r"{a}" ]

        # BACKLOG: hour formats K and k (=> https://babel.pocoo.org/en/latest/dates.html#time-fields)
        self.hour_tokens = [ r"{h}", r"{H}" ]

        self.minute_tokens = [ r"{m}", r"{mm}" ]

        self.second_tokens = [ r"{s}", r"{ss}" ]

        # generate15.py: Implement four schemas to improve the control over the time formats
        # - hours
        # - hours-minutes
        # - hours-minutes-seconds
        # - hours-minutes-seconds-microseconds
        # - hours-minutes-seconds-microseconds-timezone
        # - hours-minutes-seconds-timezone

        # DOC: https://babel.pocoo.org/en/latest/dates.html#time-fields
        # NOTE: {a} is the period (AM or PM), which is required for short hours (unless it was forgotten)
        self.format_spec = { 

            "hours" : [
                 r"{h}{whitespace}{a}", # short, no minutes, with AM or PM
                 r"{H}", # short, no minutes (added generate6)

            ],

            "hours-minutes" : [
                 r"{h}{separator}{mm}{whitespace}{a}", # short, no seconds, with AM or PM
                 r"{h}{whitespace}{a}{whitespace}{mm}", # short, no seconds
                 r"{H}{separator}{mm}", # short, no seconds
                 r"{h}{separator}{m}{whitespace}{a}",
                 r"{h}{whitespace}{a}{whitespace}{m}",
                 r"{H}{separator}{m}", # short, no seconds

            ],

            "hours-minutes-seconds" : [
                 r"{h}{separator}{mm}{separator}{ss}{whitespace}{a}", # medium
                 r"{h}{whitespace}{a}{whitespace}{mm}{separator}{ss}", # medium
                 r"{H}{separator}{mm}{separator}{ss}", # medium
                 r"{H}{separator}{mm}{separator}{ss}{whitespace}{a}", # medium
                 r"{h}{separator}{m}{separator}{ss}{whitespace}{a}",
                 r"{h}{whitespace}{a}{whitespace}{m}{separator}{ss}",
                 r"{H}{separator}{m}{separator}{ss}", # medium
                 r"{H}{separator}{m}{separator}{ss}{whitespace}{a}",
                 r"{h}{separator}{mm}{separator}{s}{whitespace}{a}",
                 r"{h}{whitespace}{a}{whitespace}{mm}{separator}{s}",
                 r"{H}{separator}{mm}{separator}{s}", # medium
                 r"{H}{separator}{mm}{separator}{s}{whitespace}{a}", # medium
                 r"{h}{separator}{m}{separator}{s}{whitespace}{a}", # medium
                 r"{h}{whitespace}{a}{whitespace}{m}{separator}{s}",
                 r"{H}{separator}{m}{separator}{s}", # medium
                 r"{H}{separator}{m}{separator}{s}{whitespace}{a}" # medium
            ],

            "hours-minutes-seconds-microseconds" : [
                 
                 r"{h}{separator}{mm}{separator}{ss}.{microsecond}{whitespace}{a}", # medium
                 r"{H}{separator}{mm}{separator}{ss}.{microsecond}",
                 r"{h}{separator}{m}{separator}{ss}.{microsecond}{whitespace}{a}", # medium
                 r"{H}{separator}{m}{separator}{ss}.{microsecond}",
                 r"{h}{separator}{mm}{separator}{s}.{microsecond}{whitespace}{a}",
                 r"{H}{separator}{mm}{separator}{s}.{microsecond}",
                 r"{h}{separator}{m}{separator}{s}.{microsecond}{whitespace}{a}", # medium
                 r"{H}{separator}{m}{separator}{s}.{microsecond}" # medium
            ],

            "hours-minutes-seconds-microseconds-timezone" : [
                 
                 r"{h}{separator}{mm}{separator}{ss}.{microsecond}{whitespace}{a}{whitespace}{timezone}", # long
                 r"{H}{separator}{mm}{separator}{ss}.{microsecond}{whitespace}{timezone}",
                 r"{h}{separator}{m}{separator}{ss}.{microsecond}{whitespace}{a}{whitespace}{timezone}",
                 r"{H}{separator}{m}{separator}{ss}.{microsecond}{whitespace}{timezone}",
                 r"{h}{separator}{mm}{separator}{s}.{microsecond}{whitespace}{a}{whitespace}{timezone}",
                 r"{H}{separator}{mm}{separator}{s}.{microsecond}{whitespace}{timezone}",
                 r"{h}{separator}{m}{separator}{s}.{microsecond}{whitespace}{a}{whitespace}{timezone}", # long
                 r"{H}{separator}{m}{separator}{s}.{microsecond}{whitespace}{timezone}" # long
                 
            ],

            "hours-minutes-seconds-timezone" : [
                 r"{h}{separator}{mm}{separator}{ss}{whitespace}{a}{whitespace}{timezone}",
                 r"{h}{whitespace}{a}{whitespace}{mm}{separator}{ss}{whitespace}{timezone}",
                 r"{H}{separator}{mm}{separator}{ss}{whitespace}{timezone}",
                 r"{H}{separator}{mm}{separator}{ss}{whitespace}{a}{whitespace}{timezone}", # long
                 r"{h}{separator}{m}{separator}{ss}{whitespace}{a}{whitespace}{timezone}",
                 r"{h}{whitespace}{a}{whitespace}{m}{separator}{ss}{whitespace}{timezone}",
                 r"{H}{separator}{m}{separator}{ss}{whitespace}{timezone}",
                 r"{H}{separator}{m}{separator}{ss}{whitespace}{a}{whitespace}{timezone}",
                 r"{h}{separator}{mm}{separator}{s}{whitespace}{a}{whitespace}{timezone}",
                 r"{h}{whitespace}{a}{whitespace}{mm}{separator}{s}{whitespace}{timezone}",
                 r"{H}{separator}{mm}{separator}{s}{whitespace}{timezone}", # long
                 r"{H}{separator}{mm}{separator}{s}{whitespace}{a}{whitespace}{timezone}",
                 r"{h}{separator}{m}{separator}{s}{whitespace}{a}{whitespace}{timezone}", # long
                 r"{h}{whitespace}{a}{whitespace}{m}{separator}{s}{whitespace}{timezone}", # long
                 r"{H}{separator}{m}{separator}{s}{whitespace}{timezone}", # long
                 r"{H}{separator}{m}{separator}{s}{whitespace}{a}{whitespace}{timezone}" # long
                 
                 

            ]

        }

        self.all_schemas = list(self.format_spec.keys())

        # auto check duplicate formats
        _schema_formats = []
        for schema_name, schema_formats in self.format_spec.items():
            for schema_format in schema_formats:
                if schema_format in _schema_formats:
                    raise ValueError(f"schema_format '{schema_format}' in schema '{schema_name}' exists more than once")
                
                _schema_formats.append(schema_format)
            
        module_logger.info(f"No duplicates found in formats for all {len(self.all_schemas)} schemas")
       
    def generate(self
                , output : str
                , num_observations : int
                , start_date : datetime = None 
                , schemas : List[str] = None
                , locale_schema : str = None
                ) -> Iterator[ Tuple[ TrainingPair, datetime] ]:

        """

        :param output: what do generate: iso8601, parsestr

        :param num_observations: number of dates to generate; each date will be generated in N(locales) and N(format_spec)

        :param start_date: optional; start date(time) of the dates; a default value will be generated if None

        :return: function is a generator -> an iterator of 2-tuples
            1. TrainingPairs (namedtuple)
            2. the input date

        """

        assert isinstance(output, str)

        # generate15: resolve schemas to be used
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
        
        # set start date
        if start_date is None:
            start_date = datetime(1990, 1, 1, 0, 0, 0)

        d = start_date

        # built-in formats
        for idx in range(0, num_observations):

            aux = {}

            # generate11: generate a random time in the range [start_date; ...] with UTC timezone
            dt_utc = random_utc_datetime(start_date)

            # generate11: iterate on timezones
            # NOTE: calls to astimezone() on certain dates generate OverflowError errors
            # HACK: select another timezone if this conversion does not work
            d = None
            while d is None:
                
                this_timezone_name = choice(all_timezones)
                try:
                    this_timezone =  timezone(this_timezone_name)

                    # move the UCT datetime to this timezone
                    d = dt_utc.astimezone(this_timezone)
                
                except OverflowError as e:
                    if self.debug:
                        module_logger.warning(f"Error setting timezone ({e}) => trying again")
                    
                    pass

            
         
            locale = choice(self.locales)
                
            # generate15: choose a random schema from the schema shortlist
            schema = choice(schemas)
            raw_format_spec = choice(self.format_spec[schema])
            separator_character = choice(self.separators)

            aux["schema"] = schema
            aux["raw_format_spec"] = raw_format_spec

            # generate12: iterate on microsecond format
            microsecond_format = choice(self.microsecond_formats)

            # generate14: iterate on timezone formats
            timezone_format = choice(self.timezone_formats)
                        
            # {whitespace} token is replaced with the values from whitespace_characters
            format_spec = raw_format_spec.replace(r"{whitespace}", self.whitespace_character)

            # replace {separator} token with some token
            format_spec = format_spec.replace(r"{separator}", separator_character)

            # generate12: replace {microsecond} token with some token
            # NOTE: microsecond_format already contains encapsulating curly braces
            format_spec = format_spec.replace(r"{microsecond}", microsecond_format)

            # generate14: replace {timezone} token with some token
            # NOTE: microsecond_format already contains encapsulating curly braces
            format_spec = format_spec.replace(r"{timezone}", timezone_format)

            # generate 17: apply custom formatting before Babel
            # NOTE: custom_formatter also applies Babel formatting
            input_str_unicode = self.custom_formatter.apply(format_spec, d, locale=locale)
        
            # BUG FIX | generate10 | not all outputs applied normalisation
            # => apply full normalisation
            # 1. unicode
            # 2. tokens (e.g convert .. to .)
            # 3. whitespace (e.g "\u202f" to " ")
            # 4. convert to lower case

            # mod | for normalisation of the input string, use the normalisation in custom formatter 
            #input_str = self.normalise_whitespace.normalise(self.normalise_tokens.normalise(self.normalise_unicode.normalise(input_str_unicode))).lower()
            input_str = self.custom_formatter.normalise_string(input_str_unicode)

            # the output can be specified
            # for NER (named entity resolution)
            if output == "entity": 
                output_str = self.entity

            elif output == "separator":     # added in generate7
                output_str = separator_character

            elif output == "format_spec": 
                output_str = format_spec

            elif output == "format": 
                output_str = format_spec

            elif output == "schema": 
                output_str = schema

            elif output == "raw_format_spec": 
                output_str = raw_format_spec

            elif output == "year":
                output_str = "-1"

            # generate5: additional outputs
            elif output == "hour":
                output_str = str(d.hour)
            
            elif output == "minute":
                output_str = str(d.minute)

            elif output == "second":
                # NOTE: only output seconds if there are seconds in the string
                # for example, if the input string is 13:23, the target seconds must be truncated to 0
                if r"{ss}" in raw_format_spec:
                    output_str = str(d.second)
                else:
                    output_str = "00"

            elif output == "type":
                # predict the core datalake types, defined in datalake/config.py
                # DATE, DATETIME, STR, INT, FLOAT, BOOL, LONG
                output_str = "TIME"

            elif output == "iso8601":
                output_str = format_time(d, locale=locale, format=self.iso_format_date)

            elif output == "parsestr":
                output_str = format_spec

           
            elif output == "model":

                # important: do not normalise the input string when predicting the model
                # this is because when use the meta OVR models, we are using the raw strings to predict types
                # however, when predicting the parsing string (e.g normparsestr), then we already know that the type is a time
                # so we can then normalise 
                output_str = self.model_name

            elif output == "normparsestr":

                # normalised parse string
                # 1. normalised whitespace
                # 2. normalised tokens
                output_str = self.normalise_ldml_tokens.normalise(self.normalise_whitespace.normalise(format_spec))

                # important: input date also need needs to be normalised with the same normalisation algorithm
                # this is what will happen after training when predicting formats in production
                input_str = self.normalise_whitespace.normalise(input_str)
            
            elif output == "tokens":

                # important: remove single quotes that were used to escape characters for Babel
                # the raw format could be something like this: e.g {day} {month} {year} 'at' {hour}:{minute}:{second} {zzzz}"
                # we used 'at' to tell Babel not to interpet "at"
                # but now we need to remove these single escape quotes, else parsing string won't work in parse library
                target_format = format_spec.replace("'", "")
                
                # get the value generated by Babel for each token, and assess if it contains spaces
                # if so, create as many tokens as necessary
                # example:
                # {timezone} -> Hora Coordenada Universal -> {timezone.0} {timezone.1} {timezone.2}
                for part in target_format.split('{'):
                    # get the token
                    token = part.split('}')[0]
                    if len(token):

                        # get value of this token, using Babel to format it
                        value = format_time(d, locale=locale, format=token)

                        # HACK: Babel generates \xa0 in certain periods, a. m.
                        # replace them with space, otherwise the split opertion will NOT split the string since it is only splitting on space character
                        # backlog: use normalise_whitespace?
                        value = value.replace(u'\xa0', u' ')

                        # count number of elements
                        elements = value.split(' ')
                        num_elements = len(elements)

                        if num_elements >= 2:
                            # important: translate the LDML token to the simplified token
                            #target_token = ' '.join( [ "{" + token + "." + str(idx) + "}" for idx in range(num_elements) ] )
                            target_token = ' '.join( [ "{" + self.normalise_ldml_tokens.ldml_tokens[token] + "." + str(idx) + "}" for idx in range(num_elements) ] )
                            target_format = target_format.replace("{" + token + "}", target_token)

                
                # normalised parse string
                # 1. normalised whitespace
                # 2. normalised tokens
                # CAREFUL! apply token normalisation first as normalise_whitespace will cast the string to lower case, which will render the M token ambigusous (month or minutes)
                output_str = self.normalise_whitespace.normalise(self.normalise_ldml_tokens.normalise(target_format))

                # important: input date also need needs to be normalised with the same normalisation algorithm
                # this is what will happen after training when predicting formats in production
                #input_str = self.normalise_whitespace.normalise(input_str)

                # cleanup tokens in the input string; example: 1.jan..00 12:00 am -> 1.jan.00 12:00 am
                input_str = self.normalise_whitespace.normalise(self.normalise_tokens.normalise(input_str))

            else:
                raise RuntimeError(f"unhandled output '{output}'")
            

            if self.debug:
                print(f"{idx} / {num_observations} | {d} | {locale} | {format_spec} | {input_str} | {output_str}")

            yield (TrainingPair(input_str, output_str, locale, aux=aux), d)

# -----
# main
# -----

if __name__ == "__main__":

    from argparse import ArgumentParser

    def main():

        # --- command line args ---
        cmd_line_parser = ArgumentParser(description='driver for Generate')
        cmd_line_parser.add_argument('output', type=str, default=None, help='iso8601, parsestr, model')
        cmd_line_parser.add_argument('num_observations', type=int, default=None, help='number of observations to generate')
        
        # arguments
        cmd_line_parser.add_argument('--start_date', type=str, help='start datetime', default=None)
        cmd_line_parser.add_argument('--schemas', type=str, help='comma separated list if schemas to use', default=None)

        cmd_line_parser.add_argument('--inputs', default=False, dest='inputs', action='store_true', help='show inputs only')
        cmd_line_parser.add_argument('--outputs', default=False, dest='outputs', action='store_true', help='show outputs (targets) only')
        cmd_line_parser.add_argument('--targets', default=False, dest='outputs', action='store_true', help='show outputs (targets) only')
        
        cmd_line_parser.add_argument('--debug', default=False, dest='debug', action='store_true', help='debugging')
        args = cmd_line_parser.parse_args()

        # create generator
        generator = Generate()
        generator.debug = args.debug

        start_date = datetime.fromisoformat(args.start_date) if args.start_date is not None else None
        print(f"start_date from arguments : {start_date}")
        print(f"args.inputs : {args.inputs}")
        print(f"args.outputs : {args.outputs}")

        # optional: specify schema(s)
        schemas = None
        if args.schemas is not None:
            schemas = [schema.strip() for schema in args.schemas.split(",")]
            print(f"schemas : {schemas}")

        results = generator.generate(args.output
                                     , args.num_observations
                                     , start_date=start_date
                                     , schemas=schemas
                                     )

        # show output
        for idx, (training_pair, _) in enumerate(results, start=1):
            if not args.inputs and not args.outputs:
                print(training_pair)
            elif args.inputs:
                print(training_pair.input)
            elif args.outputs:
                print(training_pair.output)
            

    main()