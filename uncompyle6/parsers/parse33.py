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

        whileTruestmt ::= SETUP_LOOP l_stmts JUMP_ABSOLUTE
                          JUMP_BACK COME_FROM_LOOP

        # Python 3.5+ has jump optimization to remove the redundant
        # jump_excepts. But in 3.3 we need them added

        trystmt     ::= SETUP_EXCEPT suite_stmts_opt POP_BLOCK
                        try_middle
                        jump_excepts come_from_except_clauses
        """

    def add_custom_rules(self, tokens, customize):
        self.remove_rules("""
        # 3.3+ adds POP_BLOCKS
        whileTruestmt ::= SETUP_LOOP l_stmts JUMP_ABSOLUTE JUMP_BACK COME_FROM_LOOP
        whileTruestmt ::= SETUP_LOOP l_stmts_opt JUMP_BACK COME_FROM_LOOP
        whileTruestmt ::= SETUP_LOOP l_stmts_opt JUMP_BACK NOP COME_FROM_LOOP
        whileTruestmt ::= SETUP_LOOP l_stmts_opt JUMP_BACK POP_BLOCK NOP COME_FROM_LOOP
        whilestmt     ::= SETUP_LOOP testexpr l_stmts_opt JUMP_BACK
                          POP_BLOCK JUMP_ABSOLUTE COME_FROM_LOOP
        """)
        super(Python33Parser, self).add_custom_rules(tokens, customize)
        return

class Python33ParserSingle(Python33Parser, PythonParserSingle):
    pass
