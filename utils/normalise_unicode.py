# -*- coding: utf-8 -*-

"""
normalise_unicode.py: normalise the tokens in a string to ASCII, e.g da manhã -> da manha

Translate non-ASCII unicode characters to their equivalent ACSCI counterpart using NFKD

From wikipedia: Unicode equivalence is the specification by the Unicode character encoding standard that 
some sequences of code points represent essentially the same character. 
This feature was introduced in the standard to allow compatibility with preexisting standard character sets, 
which often included similar or identical characters. 
BACKLOG
"""

from unicodedata import normalize

from utils.check_isinstance import check_isinstance

class NormaliseUnicode:
    """
    NormaliseUnicode: normalise the tokens in a string to ASCII.
    """

   
       
    
    def normalise(self, input_str : str) -> str:
        
        """
        translate input_str to ASCII

        :param input_str: a Unicode string

        :return: ASCII string

        """

        # argument checks
        check_isinstance(input_str, str)

        # NOTE: it seems the unicode x character used by Babel for exponents does not get translated by the normalize NFKD
        # => manual override
        # e.g "8,531523381499447×10^+7"
        if "×" in input_str:
            input_str = input_str.replace("×", "x")

        # device control 4 (ascii code 20)
        #if chr(20) in input_str:
        #    print(f"FOUND 20!!")
        #    input_str = input_str.replace(chr(20), " ")

        # string.encode() creates a byte string, which cannot be mixed with a regular string.
        # You have to convert the result back to a string again; the method is predictably called decode.
        # src: https://stackoverflow.com/questions/51710082/what-does-unicodedata-normalize-do-in-python
        return normalize(u'NFKD', input_str).encode('ascii', 'ignore').decode('ascii')

   
