#  Copyright (c) 2016 Rocky Bernstein
"""
spark grammar differences over Python 3.1 for Python 3.0.
"""
from __future__ import print_function

from uncompyle6.parser import PythonParserSingle
from uncompyle6.parsers.parse31 import Python31Parser

class Python30Parser(Python31Parser):

    def p_30(self, args):
        """
        # Store locals is only in Python 3.0 to 3.3
        stmt ::= store_locals
        store_locals ::= LOAD_FAST STORE_LOCALS

        jmp_true ::= JUMP_IF_TRUE_OR_POP POP_TOP
        _ifstmts_jump ::= c_stmts_opt JUMP_FORWARD POP_TOP COME_FROM
        """

class Python31ParserSingle(Python31Parser, PythonParserSingle):
    pass
