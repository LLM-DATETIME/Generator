# -*- coding: utf-8 -*-
"""
isalpha_or_spaces.py: return True if a string is comprised of only alphabetic characeters and/or spaces

example: "hora coordenada universal" will return True

src: https://stackoverflow.com/questions/20890618/isalpha-python-function-wont-consider-spaces

edward | 2021-09-09
"""


def isalpha_or_spaces(s : str):
    return all(x.isalpha() or x.isspace() for x in s)

