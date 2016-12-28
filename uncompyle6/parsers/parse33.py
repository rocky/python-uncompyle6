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
        expr          ::= yield_from
        yield_from    ::= expr expr YIELD_FROM

        # We do the grammar hackery below for semantics
        # actions that want c_stmts_opt at index 1

        iflaststmt    ::= testexpr c_stmts_opt33
        c_stmts_opt33 ::= JUMP_BACK JUMP_ABSOLUTE c_stmts_opt
        _ifstmts_jump ::= c_stmts_opt JUMP_FORWARD _come_from
        """

class Python33ParserSingle(Python33Parser, PythonParserSingle):
    pass
