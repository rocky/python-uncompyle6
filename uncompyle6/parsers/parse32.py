#  Copyright (c) 2016 Rocky Bernstein
"""
spark grammar differences over Python 3 for Python 3.2.
"""
from __future__ import print_function

from uncompyle6.parser import PythonParserSingle
from uncompyle6.parsers.parse3 import Python3Parser

class Python32Parser(Python3Parser):
    def p_32to35(self, args):
        """
        # Store locals is only in Python 3.0 to 3.3
        stmt ::= store_locals
        store_locals ::= LOAD_FAST STORE_LOCALS

        # Python < 3.5 no POP BLOCK
        whileTruestmt     ::= SETUP_LOOP l_stmts_opt JUMP_BACK
                              COME_FROM_LOOP
        whileTruestmt     ::= SETUP_LOOP return_stmts
                              COME_FROM_LOOP

        try_middle ::= JUMP_FORWARD COME_FROM_EXCEPT except_stmts
                       END_FINALLY

        # Python 3.2+ has more loop optimization that removes
        # JUMP_FORWARD in some cases, and hence we also don't
        # see COME_FROM
        _ifstmts_jump ::= c_stmts_opt
        _ifstmts_jump ::= c_stmts_opt JUMP_FORWARD _come_from

        stmt           ::= del_deref_stmt
        del_deref_stmt ::= DELETE_DEREF
        """
    pass

    def p_32on(self, args):
        """
        # In Python 3.2+, DUP_TOPX is DUP_TOP_TWO
        binary_subscr2 ::= expr expr DUP_TOP_TWO BINARY_SUBSCR
        """
        pass

    def add_custom_rules(self, tokens, customize):
        super(Python32Parser, self).add_custom_rules(tokens, customize)
        for i, token in enumerate(tokens):
            opname = token.type
            if opname.startswith('MAKE_FUNCTION_A'):
                args_pos, args_kw, annotate_args  = token.attr
                # Check that there are 2 annotated params?
                rule = (('mkfunc_annotate ::= %s%sannotate_tuple '
                         'LOAD_CONST LOAD_CONST EXTENDED_ARG %s') %
                        (('pos_arg ' * (args_pos)),
                         ('annotate_arg ' * (annotate_args-1)), opname))
                self.add_unique_rule(rule, opname, token.attr, customize)
                pass
            return
        pass


class Python32ParserSingle(Python32Parser, PythonParserSingle):
    pass
