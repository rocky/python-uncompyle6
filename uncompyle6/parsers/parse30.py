#  Copyright (c) 2016-2017 Rocky Bernstein
"""
spark grammar differences over Python 3.1 for Python 3.0.
"""
from __future__ import print_function

from uncompyle6.parser import PythonParserSingle
from uncompyle6.parsers.parse31 import Python31Parser

class Python30Parser(Python31Parser):

    def p_30(self, args):
        """

        assert            ::= assert_expr jmp_true LOAD_ASSERT RAISE_VARARGS_1 COME_FROM POP_TOP
        return_if_lambda  ::= RETURN_END_IF_LAMBDA COME_FROM POP_TOP
        compare_chained2  ::= expr COMPARE_OP RETURN_END_IF_LAMBDA

        # FIXME: combine with parse3.2
        whileTruestmt     ::= SETUP_LOOP l_stmts_opt JUMP_BACK
                              COME_FROM_LOOP
        whileTruestmt     ::= SETUP_LOOP returns
                              COME_FROM_LOOP

        # In many ways Python 3.0 code generation is more like Python 2.6 than
        # it is 2.7 or 3.1. So we have a number of 2.6ish (and before) rules below
        # Specifically POP_TOP is more prevelant since there is no POP_JUMP_IF_...
        # instructions

        _ifstmts_jump  ::= c_stmts JUMP_FORWARD _come_froms POP_TOP COME_FROM
        _ifstmts_jump  ::= c_stmts COME_FROM POP_TOP

        # Used to keep index order the same in semantic actions
        jb_pop_top     ::= JUMP_BACK _come_froms POP_TOP

        while1stmt     ::= SETUP_LOOP l_stmts COME_FROM_LOOP
        whileelsestmt  ::= SETUP_LOOP testexpr l_stmts
                           jb_pop_top POP_BLOCK
                           else_suitel COME_FROM_LOOP
        # while1elsestmt ::= SETUP_LOOP l_stmts
        #                    jb_pop_top POP_BLOCK
        #                    else_suitel COME_FROM_LOOP

        else_suitel ::= l_stmts COME_FROM_LOOP JUMP_BACK

        ifelsestmtl ::= testexpr c_stmts_opt jb_pop_top else_suitel
        iflaststmtl ::= testexpr c_stmts_opt jb_pop_top
        iflaststmt  ::= testexpr c_stmts_opt JUMP_ABSOLUTE COME_FROM POP_TOP

        jf_cf_pop   ::= JUMP_FORWARD come_froms POP_TOP
        ifelsestmt  ::= testexpr c_stmts_opt jf_cf_pop else_suite COME_FROM

        withasstmt    ::= expr setupwithas store suite_stmts_opt
                          POP_BLOCK LOAD_CONST COME_FROM_FINALLY
                          LOAD_FAST DELETE_FAST WITH_CLEANUP END_FINALLY
        setupwithas   ::= DUP_TOP LOAD_ATTR STORE_FAST LOAD_ATTR CALL_FUNCTION_0 setup_finally
        setup_finally ::= STORE_FAST SETUP_FINALLY LOAD_FAST DELETE_FAST

        # Need to keep LOAD_FAST as index 1
        set_comp_func_header ::=  BUILD_SET_0 DUP_TOP STORE_FAST
        set_comp_func ::= set_comp_func_header
                          LOAD_FAST FOR_ITER store comp_iter
                          JUMP_BACK POP_TOP JUMP_BACK RETURN_VALUE RETURN_LAST

        list_comp_header ::= BUILD_LIST_0 DUP_TOP STORE_FAST
        list_comp        ::= list_comp_header
                             LOAD_FAST FOR_ITER store comp_iter
                             JUMP_BACK

        set_comp_header  ::= BUILD_SET_0 DUP_TOP STORE_FAST
        set_comp         ::= set_comp_header
                             LOAD_FAST FOR_ITER store comp_iter
                             JUMP_BACK

        dict_comp_header ::= BUILD_MAP_0 DUP_TOP STORE_FAST
        dict_comp        ::= dict_comp_header
                             LOAD_FAST FOR_ITER store dict_comp_iter
                             JUMP_BACK

        dict_comp_iter   ::= expr expr ROT_TWO expr STORE_SUBSCR

        # JUMP_IF_TRUE POP_TOP as a replacement
        comp_if       ::= expr jmp_false comp_iter
        comp_if       ::= expr jmp_false comp_iter JUMP_BACK COME_FROM POP_TOP
        comp_if_not   ::= expr jmp_true  comp_iter JUMP_BACK COME_FROM POP_TOP
        comp_iter     ::= expr expr SET_ADD
        comp_iter     ::= expr expr LIST_APPEND

        jump_forward_else     ::= JUMP_FORWARD COME_FROM POP_TOP
        jump_absolute_else    ::= JUMP_ABSOLUTE COME_FROM POP_TOP
        except_suite          ::= c_stmts POP_EXCEPT jump_except POP_TOP
        except_suite_finalize ::= SETUP_FINALLY c_stmts_opt except_var_finalize END_FINALLY
                                  _jump COME_FROM POP_TOP

        _ifstmts_jump         ::= c_stmts_opt JUMP_FORWARD COME_FROM POP_TOP

        jump_except           ::= JUMP_FORWARD COME_FROM POP_TOP
        jump_except           ::= JUMP_ABSOLUTE COME_FROM POP_TOP
        or                    ::= expr jmp_false expr jmp_true expr
        or                    ::= expr jmp_true expr

        ################################################################################
        # In many ways 3.0 is like 2.6. One similarity is there is no JUMP_IF_TRUE and
        # JUMP_IF_FALSE
        # The below rules in fact are the same or similar.

        jmp_true         ::= JUMP_IF_TRUE POP_TOP
        jmp_false        ::= JUMP_IF_FALSE _come_froms POP_TOP
        jmp_false_then   ::= JUMP_IF_FALSE POP_TOP

        # We don't have hacky THEN detection, so we do it
        # in the grammar below which is also somewhat hacky.

        stmt             ::= ifstmt30
        ifstmt30         ::= testexpr_then _ifstmts_jump30

        testexpr_then    ::= testfalse_then
        testfalse_then   ::= expr jmp_false_then
        call_stmt        ::= expr COME_FROM
        _ifstmts_jump30  ::= c_stmts POP_TOP

        gen_comp_body    ::= expr YIELD_VALUE COME_FROM POP_TOP

        except_handler   ::= jmp_abs COME_FROM_EXCEPT except_stmts
                             COME_FROM POP_TOP END_FINALLY

        expr             ::= or30
        ret_or           ::= or30
        or30             ::= expr JUMP_IF_TRUE COME_FROM POP_TOP expr come_from_opt

        ################################################################################
        for_block      ::= l_stmts_opt _come_froms POP_TOP JUMP_BACK

        except_handler ::= JUMP_FORWARD COME_FROM_EXCEPT except_stmts
                           POP_TOP END_FINALLY come_froms
        except_handler ::= jmp_abs COME_FROM_EXCEPT except_stmts
                           POP_TOP END_FINALLY

        return_if_stmt ::= ret_expr RETURN_END_IF COME_FROM POP_TOP
        and            ::= expr jmp_false expr come_from_opt
        whilestmt      ::= SETUP_LOOP testexpr l_stmts_opt come_from_opt
                           JUMP_BACK come_froms POP_TOP POP_BLOCK COME_FROM_LOOP
        whilestmt      ::= SETUP_LOOP testexpr returns
                           POP_TOP POP_BLOCK COME_FROM_LOOP



        # compare_chained is like x <= y <= z
        compare_chained1  ::= expr DUP_TOP ROT_THREE COMPARE_OP
                              jmp_false compare_chained1 _come_froms
        compare_chained1  ::= expr DUP_TOP ROT_THREE COMPARE_OP
                              jmp_false compare_chained2 _come_froms
        compare_chained2 ::= expr COMPARE_OP RETURN_END_IF
        """

    def customize_grammar_rules(self, tokens, customize):
        super(Python30Parser, self).customize_grammar_rules(tokens, customize)
        self.remove_rules("""
        iflaststmtl        ::= testexpr c_stmts_opt JUMP_BACK COME_FROM_LOOP
        ifelsestmtl        ::= testexpr c_stmts_opt JUMP_BACK else_suitel
        iflaststmt         ::= testexpr c_stmts_opt JUMP_ABSOLUTE
        _ifstmts_jump      ::= c_stmts_opt JUMP_FORWARD _come_froms
        jump_forward_else  ::= JUMP_FORWARD ELSE
        jump_absolute_else ::= JUMP_ABSOLUTE ELSE
        whilestmt          ::= SETUP_LOOP testexpr l_stmts_opt COME_FROM JUMP_BACK POP_BLOCK
                               COME_FROM_LOOP
        whilestmt          ::= SETUP_LOOP testexpr returns
                               POP_BLOCK COME_FROM_LOOP
        assert             ::= assert_expr jmp_true LOAD_ASSERT RAISE_VARARGS_1
        return_if_lambda   ::= RETURN_END_IF_LAMBDA
        except_suite       ::= c_stmts POP_EXCEPT jump_except
        whileelsestmt      ::= SETUP_LOOP testexpr l_stmts JUMP_BACK POP_BLOCK
                               else_suitel COME_FROM_LOOP

        # No JUMP_IF_FALSE_OR_POP, JUMP_IF_TRUE_OR_POP,
        # POP_JUMP_IF_FALSE, or POP_JUMP_IF_TRUE

        jmp_false        ::= POP_JUMP_IF_FALSE
        jmp_true         ::= JUMP_IF_TRUE_OR_POP POP_TOP
        compare_chained1 ::= expr DUP_TOP ROT_THREE COMPARE_OP JUMP_IF_FALSE_OR_POP
                             compare_chained1 COME_FROM
        compare_chained1 ::= expr DUP_TOP ROT_THREE COMPARE_OP JUMP_IF_FALSE_OR_POP
                             compare_chained2 COME_FROM
        ret_or           ::= expr JUMP_IF_TRUE_OR_POP ret_expr_or_cond COME_FROM
        or               ::= expr JUMP_IF_TRUE_OR_POP expr COME_FROM
        """)

        self.check_reduce["iflaststmtl"] = "AST"
        self.check_reduce['ifstmt'] = "AST"
        # self.check_reduce["ifelsestmt"] = "AST"
        return

    def reduce_is_invalid(self, rule, ast, tokens, first, last):
        invalid = super(Python30Parser,
                        self).reduce_is_invalid(rule, ast,
                                                tokens, first, last)
        if invalid:
            return invalid
        if (
            rule[0] in ("iflaststmtl", "ifstmt") and ast[0] == "testexpr"
        ):
            testexpr = ast[0]
            if testexpr[0] == "testfalse":
                testfalse = testexpr[0]
                if testfalse[1] == "jmp_false":
                    jmp_false = testfalse[1]
                    if last == len(tokens):
                        last -= 1
                    while (isinstance(tokens[first].offset, str) and first < last):
                        first += 1
                    if first == last:
                        return True
                    while (first < last and isinstance(tokens[last].offset, str)):
                        last -= 1
                    return not (tokens[first].offset <= jmp_false[0].attr <= tokens[last].offset)

    pass

class Python30ParserSingle(Python30Parser, PythonParserSingle):
    pass
