#  Copyright (c) 2016, 2024 Rocky Bernstein
"""
spark grammar differences over Python 3.2 for Python 3.3.
"""

from uncompyle6.parser import PythonParserSingle
from uncompyle6.parsers.parse32 import Python32Parser


class Python33Parser(Python32Parser):
    def p_33on(self, args):
        """
        # Python 3.3+ adds yield from.
        expr          ::= yield_from
        yield_from    ::= expr expr YIELD_FROM
        stmt         ::= genexpr_func
        """

    def customize_grammar_rules(self, tokens, customize):
        self.remove_rules(
            """
        # 3.3+ adds POP_BLOCKS
        whileTruestmt ::= SETUP_LOOP l_stmts_opt JUMP_BACK POP_BLOCK NOP COME_FROM_LOOP
        whileTruestmt ::= SETUP_LOOP l_stmts_opt JUMP_BACK NOP COME_FROM_LOOP
        """
        )
        super(Python33Parser, self).customize_grammar_rules(tokens, customize)

        # FIXME: move 3.3 stuff out of parse3.py and put it here.
        # for i, token in enumerate(tokens):
        #     opname = token.kind
        #     opname_base = opname[: opname.rfind("_")]

        return


class Python33ParserSingle(Python33Parser, PythonParserSingle):
    pass
