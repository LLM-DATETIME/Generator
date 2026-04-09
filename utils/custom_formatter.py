# -*- coding: utf-8 -*-

"""
custom_formatter.py: Apply custom formats for datetimes that are not handled by Babel.

NOTES
- the rendering of custom formats should be done *before* rendering with Babel; otherwise, Babel will interpret the rendered
    - e.g the rendered number 1 => "one" will be interpreted by Babel, character 'e' is the local day of the week

    - Rendered strings are automatically escaped with single quotes so that Babel leaves them as is

    - Babel automatically removes single quotes on rendering

EXAMPLES
    {T} : timezone full name, e.g "America/Anguilla"
    {TT} : short timezone name, e.g "AST"

    {ON(day)} : ordinal number of day, e.g 1st


"""

# system
from datetime import date, datetime, time, timedelta
from typing import List, Set, Dict, Tuple, Optional, Union, Iterable

# 3rd party
import babel.dates
from num2words import num2words, CONVERTER_CLASSES as num2words_locales
from roman import toRoman

from utils.check_isinstance import check_isinstance
from utils.normalise_tokens import NormaliseTokens as NormaliseLDMLTokens
from utils.normalise_string import NormaliseString


class CustomFormatter:

    """
    CustomFormatter: Apply custom formats for datetimes that are not handled by Babel.
    """

    def __init__(self, apply_babel : bool = True, normalise : bool = True):
        """
        :param apply_babel: apply Babel format_datetime after custom formats

        :param normalise: apply full normalisation
            # 1. unicode
            # 2. tokens (e.g convert .. to .)
            # 3. whitespace (e.g "\u202f" to " ")
            # 4. convert to lower case
        
        """

        self.apply_babel = apply_babel
        self.normalise = normalise

        self.flatten_string = NormaliseString()
        self.normalise_ldml_tokens = NormaliseLDMLTokens()

        # count number of calls to babel so that we can release Babel's cache; else we create a memory leak
        # => https://github.com/python-babel/babel/issues/962
        self.babel_call_counter = 0

    def release_babel_cache(self):
        babel.dates._pattern_cache.clear()


    def add_babel_escape(self, s : str):
        """
        Add escape characters so that Babel does not interpret our rendered strings.

        doc: https://babel.pocoo.org/en/latest/numbers.html#pattern-syntax

        :param s: a string to be escaped, e.g first

        :return: escaped string, e.g 'first'
        """
        return "'" + str(s) + "'"

    def find_num2words_locale(self, locale : str, fallback : str = "en") -> str:

        """
        find_num2words_locale: find locale in num2wors closest to 'locale'
        NOTE: not all locales are available in num2words

        :param locale: input locale to be matched

        :return: locale to use in num2words;
            if no locale could be found, return fallback

        """
        if locale in num2words_locales:
            return locale

        # not found; try to use the main locale, i.e the "en" in "en_IN"
        if len(locale) == 5:
            locale = locale[0:2]

            if locale in num2words_locales:
                return locale
                
        
        # fallback        
        return fallback



    def apply(self, string_to_format : str, dt : Union[date, datetime], locale : str = "en", normalise : bool = None) -> str:

        """
        Apply custom formats for datetimes that are not handled by Babel.

        :param string_to_format: a string to format with tokens in curly brackets for rendering
            supports Babel formats such as {dd} ... and also custom formats such as "{C(day)}" ...
            ; e.g "12:37:12 {T}"

        :param dt: datetime

        :param locale: optional; locale name as a string
            may or may not be applicable for the tokens to be rendered

        :param normalise: normalise (flatten unicode, remove whitespace, ...)
            - None: use default (set in constructor)
            - True: : always normalise
            - False : never normalise
        
        :return: formatted string
        """

        check_isinstance(string_to_format, str)
        check_isinstance(dt, (date, datetime))
    
        # -- timezone --
        if r"{T}" in string_to_format:
            # if timezone is "America/Anguilla" => "America/Anguilla"
            # returns (most of the time) the original timezone name as specified in c
            string_to_format = string_to_format.replace(r"{T}", self.add_babel_escape(dt.timetz().tzname()))

        if r"{TT}" in string_to_format:
            # if timezone is "America/Anguilla" => "AST"
            string_to_format = string_to_format.replace(r"{TT}", self.add_babel_escape(dt.tzname()))

        # -- num2words --
        # C: Cardinal, e.g one
        
        if r"{C(day)}" in string_to_format:
            # NOTE: not all locales are available in num2words
            num2words_locale = self.find_num2words_locale(locale)
            string_to_format = string_to_format.replace(r"{C(day)}", self.add_babel_escape(num2words(dt.day, to="cardinal", lang=num2words_locale)))

        # O: Ordinal, e.g first
        if r"{O(day)}" in string_to_format:
            # NOTE: not all locales are available in num2words
            num2words_locale = self.find_num2words_locale(locale)
            try:
                string_to_format = string_to_format.replace(r"{O(day)}", self.add_babel_escape(num2words(dt.day, to="ordinal", lang=num2words_locale)))
            except NotImplementedError as e:
                # NOTE: not all numbers and locales work
                return str(dt.day)

        # ON: Ordinal Number, e.g 1st
        if r"{ON(day)}" in string_to_format:
            # NOTE: not all locales are available in num2words
            num2words_locale = self.find_num2words_locale(locale)
            try:
                string_to_format = string_to_format.replace(r"{ON(day)}", self.add_babel_escape(num2words(dt.day, to="ordinal_num", lang=num2words_locale)))
            except Exception as e:
                # NOTE: AttributeError: 'Num2Word_TR' object has no attribute 'to_ordinal_num'
                # NOTE: NotImplementedError
                return str(dt.day)

        # BACKLOG: add more supported word syntaxes
        # hour: "douze heures"

        # -- roman --
        
        # Roman Numerals on Month
        if r"{X(month)}" in string_to_format:
            string_to_format = string_to_format.replace(r"{X(month)}", self.add_babel_escape(toRoman(dt.month)))

        # Roman Numerals on Year
        if r"{X(year)}" in string_to_format:
            # NOTE: toRoman only supports numbers in range (must be 0..4999)
            if dt.year < 4999:
                string_to_format = string_to_format.replace(r"{X(year)}", self.add_babel_escape(toRoman(dt.year)))
            else:
                return str(dt.year)


        # apply babel formatting
        if self.apply_babel:
            babel_format_spec = string_to_format.replace("{", "").replace("}", "")
            try:
                string_to_format = babel.dates.format_datetime(dt, locale=locale, format=babel_format_spec)
            
            except KeyError as e:
                raise RuntimeError(f"Babel format '{babel_format_spec}' not found for locale '{locale}' : KeyError '{e}'")
            
            except Exception as e:
                raise e




            self.babel_call_counter += 1

            # release Babel's cache; else we create a memory leak => https://github.com/python-babel/babel/issues/962
            if (self.babel_call_counter % 1000) == 0:
                self.release_babel_cache()


        # normalise
        if normalise is True or (normalise is None and self.normalise):
            #string_to_format = self.normalise_whitespace.normalise(self.normalise_tokens.normalise(self.normalise_unicode.normalise(string_to_format))).lower().strip()
            string_to_format = self.normalise_string(string_to_format)

        return string_to_format

    def normalise_string(self, s : str, strip : bool = True, to_lower : bool = False) -> str:
        """
        normalise_string: apply full normalisation to a string

        :param s: a string to be normalised

        :param strip: True if strip should be applied as a lest step
            set to False in cases where a single whitespace character e.g ' ' is a valid normalised string that should not be stripped
            else ' ' gets stripped to ''

        :param to_lower: set to True to cast string to lower case

        :return: normalised string
        
        """
        
        s1 = self.flatten_string.normalise_string(s, to_lower=False)

        if strip:
            return s1.strip()
        else:
            return s1
    
    
   
if __name__ == '__main__':

    from argparse import ArgumentParser
    from random import choice
    from pytz import timezone, utc, all_timezones

    


    def main():

        # init command line arguments
        cmd_line_parser = ArgumentParser(description='driver for CustomFormatter')
        cmd_line_parser.add_argument('--debug', default=False, dest='debug', action='store_true', help='debugging')
        args = cmd_line_parser.parse_args()

        custom_formatter = CustomFormatter()

        locale_name = "fr"
        print("locale_name", locale_name, custom_formatter.find_num2words_locale(locale_name))

        

        dt_naive = datetime(2007, 4, 1, 12, 13, 14, 234567, tzinfo=utc) 
        print("dt_naive", dt_naive)

        tz_name = choice(all_timezones)
        print("tz_name", tz_name)

        tz = timezone(tz_name)
        print("tz", tz)

        dt = dt_naive.astimezone(tz)
        print("dt", dt)
        print("--")

        patterns = [
            # babel only
            r"{dd}-{MMM}-{yyyy} {hh}:{mm}:{ss} {ZZZZ}"

            # our own custom delimiter for timezone
            , r"{dd}-{MMM}-{yyyy} {hh}:{mm}:{ss} {T}"
            , r"{dd}-{MMM}-{yyyy} {hh}:{mm}:{ss} {TT}"

            # num2words
            , r"{C(day)}-{MMM}-{yyyy} {hh}:{mm}:{ss}"
            , r"{O(day)}-{MMM}-{yyyy} {hh}:{mm}:{ss}"
            , r"{ON(day)}-{MMM}-{yyyy} {hh}:{mm}:{ss}"

            # roman numerals
            , r"{dd}-{X(month)}-{yyyy} {hh}:{mm}:{ss}"
            , r"{dd}-{MMM}-{X(year)} {hh}:{mm}:{ss}"

            # Tmix
            , r"{C(day)}-{X(month)}}-{yyyy} {hh}:{mm}:{ss}"
            , r"{O(day)}-{X(month)}-{yyyy} {hh}:{mm}:{ss}"
            , r"{ON(day)}-{X(month)}-{X(year)} {hh}:{mm}:{ss}"
            ]
            
        for raw_format_spec in patterns:

            # NOTE: custom formatter applies Babel formatting as well
            output_string = custom_formatter.apply(raw_format_spec, dt, locale=locale_name)
            
            print(raw_format_spec, "|", output_string)

            # check no trailing curly braces in the putput string
            assert '{' not in output_string
            assert '}' not in output_string


    # main entry point
    main()