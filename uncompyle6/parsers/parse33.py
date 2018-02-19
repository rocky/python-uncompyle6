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

        # Python 3.5+ has jump optimization to remove the redundant
        # jump_excepts. But in 3.3 we need them added

        try_except  ::= SETUP_EXCEPT suite_stmts_opt POP_BLOCK
                        except_handler
                        jump_excepts come_from_except_clauses
        """

    def p_30to33(self, args):
        """
        # Store locals is only in Python 3.0 to 3.3
        stmt           ::= store_locals
        store_locals   ::= LOAD_FAST STORE_LOCALS
        """

    def customize_grammar_rules(self, tokens, customize):
        self.remove_rules("""
        # 3.3+ adds POP_BLOCKS
        whileTruestmt ::= SETUP_LOOP l_stmts_opt JUMP_BACK NOP COME_FROM_LOOP
        whileTruestmt ::= SETUP_LOOP l_stmts_opt JUMP_BACK POP_BLOCK NOP COME_FROM_LOOP
        """)
        super(Python33Parser, self).customize_grammar_rules(tokens, customize)
        return

class Python33ParserSingle(Python33Parser, PythonParserSingle):
    pass
