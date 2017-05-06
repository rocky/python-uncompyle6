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

        whileTruestmt ::= SETUP_LOOP l_stmts JUMP_ABSOLUTE
                          JUMP_BACK COME_FROM_LOOP

        # Python 3.5+ has jump optimization to remove the redundant
        # jump_excepts. But in 3.3 we need them added

        tryelsestmt ::= SETUP_EXCEPT suite_stmts_opt POP_BLOCK
                        try_middle else_suite
                        jump_excepts come_from_except_clauses

        trystmt     ::= SETUP_EXCEPT suite_stmts_opt POP_BLOCK
                        try_middle
                        jump_excepts come_from_except_clauses

        jump_excepts ::= jump_except+
        """

class Python33ParserSingle(Python33Parser, PythonParserSingle):
    pass
