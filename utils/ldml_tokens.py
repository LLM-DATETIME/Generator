# -*- coding: utf-8 -*-

"""
ldml_tokens.py: bi-directional mapping from LDML datetime tokens to simplified datalake datetime tokens

using the mapping table here: http://babel.pocoo.org/en/latest/dates.html, 

...which is based on the less readable https://unicode.org/reports/tr35/#Date_Format_Patterns

{yyyy} -> {year}

{M} -> {month}
{MM} -> {month}
{MMM} -> {month}
{MMMM} -> {month}

etc

"""

# system
from datetime import date, datetime, time, timedelta
from typing import List, Set, Dict, Tuple, Optional, Union, Iterable

class LDMLTokens(dict):

    # training configuration
    def __init__(self):

        # day, month, year
        self["d"] = "day"
        self["dd"] = "day"
        self["ddd"] = "day"
        self["dddd"] = "day"

        # careful! upper-case 'M' in LDML is used for months
        # careful! lower-case 'm' in LDML is used for minutes
        self["M"] = "month"
        self["MM"] = "month"
        self["MMM"] = "month"
        self["MMMM"] = "month"
        self["MMMMM"] = "month"

        self["L"] = "month"
        self["LL"] = "month"
        self["LLL"] = "month"
        self["LLLL"] = "month"
        self["LLLLL"] = "month"


        self["Y"] = "year"
        self["YY"] = "year"
        self["YYY"] = "year"
        self["YYYY"] = "year"

        self["y"] = "year"
        self["yy"] = "year"
        self["yyy"] = "year"
        self["yyyy"] = "year"

        # hour, minute, second
        # CAREFUL! no plural, so it is NOT hours, minutes and seconds
        self["h"] = "hour"
        self["hh"] = "hour"
        self["hhh"] = "hour"
        self["hhhh"] = "hour"

        self["H"] = "hour"
        self["HH"] = "hour"
        self["HHH"] = "hour"
        self["HHHH"] = "hour"

        # CAREFUL! upper-case 'M' in LDML is used for months
        # CAREFUL! lower-case 'm' in LDML is used for minutes
        self["m"] = "minute"
        self["mm"] = "minute"
        self["mmm"] = "minute"
        self["mmmm"] = "minute"

        self["s"] = "second"
        self["ss"] = "second"
        self["sss"] = "second"
        self["ssss"] = "second"

        self["S"] = "second"
        self["SS"] = "second"
        self["SSS"] = "second"
        self["SSSS"] = "second"

        # week
        self["w"] = "week"

        # quarter
        self["q"] = "quarter"
        self["qq"] = "quarter"
        self["qqq"] = "quarter"
        self["qqqq"] = "quarter"

        self["Q"] = "quarter"
        self["QQ"] = "quarter"
        self["QQQ"] = "quarter"
        self["QQQQ"] = "quarter"
        

        # timezone
        # Use one to three letters for the short timezone or four for the full name.
        self["z"] = "timezone"
        self["zz"] = "timezone"
        self["zzz"] = "timezone"
        self["zzzz"] = "timezone"

        # AM/PM
        # using babel name 'period' for lack of a better name
        self["a"] = "period"

        # day of week (Monday - Sunday)
        self["e"] = "weekday" # as a number, e.g 1
        self["ee"] = "weekday" # as a 2-digit number, e.g 01
        self["E"] = "weekday" # as short text, e.g Mon
        self["EEEE"] = "weekday" # as long text, e.g Monday
        
    