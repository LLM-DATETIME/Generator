# -*- coding: utf-8 -*-

"""
normalise_tokens.py: normalise the tokens in a string; for example we replace double tokens with single tokens

for example .. is replaced with ., // with /, etc

BACKLOG
"""

from utils.check_isinstance import check_isinstance

class NormaliseTokens:

    # training configuration
    def __init__(self):

        """

        :param debug: debugging
        """

        # a dict of strings to replace "what" "with"
        self.token_map = { ".." : "." }

    
    def normalise(self, input_str : str) -> str:
        
        """
        normalise the tokens in input_str

        :param input_str: a string

        :return: normalised date/datetime

        """

        # argument checks
        check_isinstance(input_str, str)

        for replace_what, replace_with in self.token_map.items():
            input_str = input_str.replace(replace_what, replace_with)

        return input_str

   
