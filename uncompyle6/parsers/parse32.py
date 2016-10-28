#  Copyright (c) 2016 Rocky Bernstein
"""
spark grammar differences over Python 3 for Python 3.2.
"""
from __future__ import print_function

from uncompyle6.parser import PythonParserSingle
from uncompyle6.parsers.parse3 import Python3Parser

class Python32Parser(Python3Parser):
    def p_32on(self, args):
        """
        # In Python 3.2+, DUP_TOPX is DUP_TOP_TWO
        binary_subscr2 ::= expr expr DUP_TOP_TWO BINARY_SUBSCR
        stmt ::= store_locals
        store_locals ::= LOAD_FAST STORE_LOCALS
        """
    pass

class Python32ParserSingle(Python32Parser, PythonParserSingle):
    pass
