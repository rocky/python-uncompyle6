#  Copyright (c) 2016-2017, 2022-2024 Rocky Bernstein
"""
spark grammar differences over Python 3 for Python 3.2.
"""
from __future__ import print_function

from uncompyle6.parser import PythonParserSingle
from uncompyle6.parsers.parse3 import Python3Parser


class Python32Parser(Python3Parser):
    def p_30to33(self, args):
        """
        # Store locals is only in Python 3.0 to 3.3
        stmt           ::= store_locals
        store_locals   ::= LOAD_FAST STORE_LOCALS
        """

    def p_gen_comp32(self, args):
        """
        genexpr_func ::= LOAD_ARG FOR_ITER store comp_iter JUMP_BACK
        """

    def p_32to35(self, args):
        """
        if_exp            ::= expr jmp_false expr jump_forward_else expr COME_FROM

        # compare_chained_right is used in a "chained_compare": x <= y <= z
        compare_chained_right ::= expr COMPARE_OP RETURN_VALUE
        compare_chained_right ::= expr COMPARE_OP RETURN_VALUE_LAMBDA

        # Python < 3.5 no POP BLOCK
        whileTruestmt  ::= SETUP_LOOP l_stmts_opt JUMP_BACK COME_FROM_LOOP

        # Python 3.5+ has jump optimization to remove the redundant
        # jump_excepts. But in 3.3 we need them added

        try_except     ::= SETUP_EXCEPT suite_stmts_opt POP_BLOCK
                           except_handler
                           jump_excepts come_from_except_clauses

        except_handler ::= JUMP_FORWARD COME_FROM_EXCEPT except_stmts
                           END_FINALLY

        tryelsestmt    ::= SETUP_EXCEPT suite_stmts_opt POP_BLOCK
                           except_handler else_suite
                           jump_excepts come_from_except_clauses

        jump_excepts   ::= jump_except+

        # Python 3.2+ has more loop optimization that removes
        # JUMP_FORWARD in some cases, and hence we also don't
        # see COME_FROM
        _ifstmts_jump ::= stmts_opt
        _ifstmts_jump ::= stmts_opt JUMP_FORWARD _come_froms
        _ifstmts_jumpl ::= c_stmts_opt
        _ifstmts_jumpl ::= c_stmts_opt JUMP_FORWARD _come_froms

        kv3       ::= expr expr STORE_MAP
        """

    pass

    def p_32on(self, args):
        """
        # In Python 3.2+, DUP_TOPX is DUP_TOP_TWO
        subscript2 ::= expr expr DUP_TOP_TWO BINARY_SUBSCR
        """
        pass

    def customize_grammar_rules(self, tokens, customize):
        self.remove_rules(
            """
        except_handler ::= JUMP_FORWARD COME_FROM except_stmts END_FINALLY COME_FROM
        except_handler ::= JUMP_FORWARD COME_FROM except_stmts END_FINALLY COME_FROM_EXCEPT
        except_handler ::= JUMP_FORWARD COME_FROM_EXCEPT except_stmts END_FINALLY COME_FROM_EXCEPT_CLAUSE
        except_handler ::= jmp_abs COME_FROM except_stmts END_FINALLY
        tryelsestmt    ::= SETUP_EXCEPT suite_stmts_opt POP_BLOCK except_handler else_suite come_from_except_clauses
        whileTruestmt  ::= SETUP_LOOP l_stmts_opt JUMP_BACK NOP COME_FROM_LOOP
        whileTruestmt  ::= SETUP_LOOP l_stmts_opt JUMP_BACK POP_BLOCK NOP COME_FROM_LOOP
        """
        )
        super(Python32Parser, self).customize_grammar_rules(tokens, customize)
        for i, token in enumerate(tokens):
            opname = token.kind
            if opname.startswith("MAKE_FUNCTION_A"):
                args_pos, _, annotate_args = token.attr
                # Check that there are 2 annotated params?
                rule = (
                    "mkfunc_annotate ::= %s%sannotate_tuple "
                    "LOAD_CONST LOAD_CODE EXTENDED_ARG %s"
                ) % (
                    ("pos_arg " * args_pos),
                    ("annotate_arg " * (annotate_args)),
                    opname,
                )
                self.add_unique_rule(rule, opname, token.attr, customize)
                pass
            return
        pass


class Python32ParserSingle(Python32Parser, PythonParserSingle):
    pass
