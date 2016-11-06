#  Copyright (c) 2016 Rocky Bernstein
"""
spark grammar differences over Python 3.2 for Python 3.1.
"""
from __future__ import print_function

from uncompyle6.parser import PythonParserSingle
from uncompyle6.parsers.parse32 import Python32Parser

class Python31Parser(Python32Parser):

    def p_31(self, args):
        """
        binary_subscr2 ::= expr expr DUP_TOPX BINARY_SUBSCR

        setupwith      ::= DUP_TOP LOAD_ATTR store LOAD_ATTR CALL_FUNCTION_0 POP_TOP
        setupwithas    ::= DUP_TOP LOAD_ATTR store LOAD_ATTR CALL_FUNCTION_0 store
        withstmt       ::= expr setupwith SETUP_FINALLY
                           suite_stmts_opt
                           POP_BLOCK LOAD_CONST COME_FROM_FINALLY
                           load del_stmt WITH_CLEANUP END_FINALLY

        # Keeps Python 3.1 withas desigator in the same position as it is in other version
        setupwithas31  ::= setupwithas SETUP_FINALLY load del_stmt

        withasstmt     ::= expr setupwithas31 designator
                           suite_stmts_opt
                           POP_BLOCK LOAD_CONST COME_FROM_FINALLY
                           load del_stmt WITH_CLEANUP END_FINALLY

        store ::= STORE_FAST
        store ::= STORE_NAME
        load  ::= LOAD_FAST
        load  ::= LOAD_NAME
        """

    def add_custom_rules(self, tokens, customize):
        super(Python31Parser, self).add_custom_rules(tokens, customize)
        for i, token in enumerate(tokens):
            opname = token.type
            if opname.startswith('MAKE_FUNCTION_A'):
                args_pos, args_kw, annotate_args  = token.attr
                # Check that there are 2 annotated params?
                # rule = ('mkfunc2 ::= %s%sEXTENDED_ARG %s' %
                #         ('pos_arg ' * (args_pos), 'kwargs ' * (annotate_args-1), opname))
                rule = ('mkfunc_annotate ::= %s%sannotate_tuple LOAD_CONST EXTENDED_ARG %s' %
                        (('pos_arg ' * (args_pos)),
                         ('annotate_arg ' * (annotate_args-1)), opname))
                self.add_unique_rule(rule, opname, token.attr, customize)
class Python31ParserSingle(Python31Parser, PythonParserSingle):
    pass
