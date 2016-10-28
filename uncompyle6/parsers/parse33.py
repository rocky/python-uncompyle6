#  Copyright (c) 2016 Rocky Bernstein
"""
spark grammar differences over Python 3.2 for Python 3.3.
"""
from __future__ import print_function

from uncompyle6.parser import PythonParserSingle
from uncompyle6.parsers.parse32 import Python32Parser

class Python33Parser(Python32Parser):

    def p_33on(self, args):
        """
        # Python 3.3+ adds yield from.
        expr ::= yield_from
        yield_from ::= expr expr YIELD_FROM
        """

class Python33ParserSingle(Python33Parser, PythonParserSingle):
    pass
