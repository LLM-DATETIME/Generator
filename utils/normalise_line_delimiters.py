# -*- coding: utf-8 -*-

"""
normalise_line_delimiters.py: normalise line delimiters, e.g \r, \n and other unicode characters

objective is to reduce the dimensionality of the space of datetime representations

base: normalise_whitespace.py

edward | 2022-01-03 | Initial version

BACKLOG
- can the replacement algorithm not be pre-compiled?
"""

# system
import argparse
import copy
from datetime import date, datetime, time, timedelta
import importlib 
import logging
import os
import string
import random
import time
from typing import List, Set, Dict, Tuple, Optional, Union, Iterable

class NormaliseLineDelimiters:

    # training configuration
    def __init__(self, normalalisation_character = '|'):

        """
        :param normalalisation_character: replace newlines characters with this character
        """

        self.normalalisation_character = normalalisation_character

        
        # BACKLOG: add more of non-trivial line delimiters
        self.characters_to_be_replaced = [
                "\n"
                , "\r"
                ]

    
    def normalise(self, s : str) -> str:
        
        """
        normalise the line delimiters in string s

        :param s: a string

        :return: normalised string

        """

        # argument checks
        assert isinstance(s, str)

        for chars in self.characters_to_be_replaced:
            s = s.replace(chars, self.normalalisation_character)

        return s
   
