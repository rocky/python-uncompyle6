#  Copyright (c) 2016-2017, 2022 Rocky Bernstein
"""
spark grammar differences over Python 3.1 for Python 3.0.
"""

from uncompyle6.parser import PythonParserSingle
from uncompyle6.parsers.parse31 import Python31Parser

class Python30Parser(Python31Parser):

    def p_30(self, args):
        """

        pt_bp             ::= POP_TOP POP_BLOCK

        assert            ::= assert_expr jmp_true LOAD_ASSERT RAISE_VARARGS_1 COME_FROM POP_TOP
        assert2           ::= assert_expr jmp_true LOAD_ASSERT expr CALL_FUNCTION_1 RAISE_VARARGS_1
                              come_froms
        call_stmt         ::= expr _come_froms POP_TOP

        return_if_lambda  ::= RETURN_END_IF_LAMBDA COME_FROM POP_TOP
        compare_chained2  ::= expr COMPARE_OP RETURN_END_IF_LAMBDA

        # FIXME: combine with parse3.2
        whileTruestmt     ::= SETUP_LOOP l_stmts_opt
                              jb_or_c COME_FROM_LOOP
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

        jump_absolute_else ::= COME_FROM JUMP_ABSOLUTE COME_FROM POP_TOP

        jump_cf_pop   ::= _come_froms _jump  _come_froms POP_TOP

        ifelsestmt  ::= testexpr c_stmts_opt jump_cf_pop else_suite COME_FROM
        ifelsestmtl ::= testexpr c_stmts_opt jump_cf_pop else_suitel
        ifelsestmtc ::= testexpr c_stmts_opt jump_absolute_else else_suitec
        ifelsestmtc ::= testexpr c_stmts_opt jump_cf_pop else_suitec

        iflaststmt  ::= testexpr c_stmts_opt JUMP_ABSOLUTE COME_FROM
        iflaststmtl ::= testexpr c_stmts_opt jb_pop_top
        iflaststmtl ::= testexpr c_stmts_opt come_froms JUMP_BACK COME_FROM POP_TOP

        iflaststmt  ::= testexpr c_stmts_opt JUMP_ABSOLUTE COME_FROM POP_TOP


        withasstmt    ::= expr setupwithas store suite_stmts_opt
                          POP_BLOCK LOAD_CONST COME_FROM_FINALLY
                          LOAD_FAST DELETE_FAST WITH_CLEANUP END_FINALLY
        setupwithas   ::= DUP_TOP LOAD_ATTR STORE_FAST LOAD_ATTR CALL_FUNCTION_0 setup_finally
        setup_finally ::= STORE_FAST SETUP_FINALLY LOAD_FAST DELETE_FAST

        # Need to keep LOAD_FAST as index 1
        set_comp_header  ::= BUILD_SET_0 DUP_TOP STORE_FAST
        set_comp_func ::= set_comp_header
                          LOAD_FAST FOR_ITER store comp_iter
                          JUMP_BACK POP_TOP JUMP_BACK RETURN_VALUE RETURN_LAST

        list_comp_header ::= BUILD_LIST_0 DUP_TOP STORE_FAST
        list_comp        ::= list_comp_header
                             LOAD_FAST FOR_ITER store comp_iter
                             JUMP_BACK
        list_comp        ::= list_comp_header
                             LOAD_FAST FOR_ITER store comp_iter
                             JUMP_BACK _come_froms POP_TOP JUMP_BACK

        list_for         ::= DUP_TOP STORE_FAST
                             expr_or_arg
                             FOR_ITER
                             store list_iter jb_or_c

        set_comp         ::= set_comp_header
                             LOAD_FAST FOR_ITER store comp_iter
                             JUMP_BACK

        dict_comp_header ::= BUILD_MAP_0 DUP_TOP STORE_FAST
        dict_comp        ::= dict_comp_header
                             LOAD_FAST FOR_ITER store dict_comp_iter
                             JUMP_BACK
        dict_comp        ::= dict_comp_header
                             LOAD_FAST FOR_ITER store dict_comp_iter
                             JUMP_BACK _come_froms POP_TOP JUMP_BACK

        dict_comp_func   ::= BUILD_MAP_0
                             DUP_TOP STORE_FAST
                             LOAD_ARG FOR_ITER store
                             dict_comp_iter JUMP_BACK RETURN_VALUE RETURN_LAST

        stmt         ::= try_except30
        try_except30 ::= SETUP_EXCEPT suite_stmts_opt
                        _come_froms pt_bp
                         except_handler opt_come_from_except

        # From Python 2.6


	lc_body     ::= LOAD_FAST expr LIST_APPEND
        lc_body     ::= LOAD_NAME expr LIST_APPEND
        list_if     ::= expr jmp_false_then list_iter
        list_if_not ::= expr jmp_true list_iter JUMP_BACK come_froms POP_TOP
        list_iter   ::= list_if JUMP_BACK
        list_iter   ::= list_if JUMP_BACK _come_froms POP_TOP

        #############

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

        except_handler        ::= jmp_abs COME_FROM_EXCEPT except_stmts END_FINALLY

        _ifstmts_jump         ::= c_stmts_opt JUMP_FORWARD COME_FROM POP_TOP
        _ifstmts_jump         ::= c_stmts_opt come_froms POP_TOP JUMP_FORWARD _come_froms

        jump_except           ::= _jump COME_FROM POP_TOP

        expr_jt               ::= expr jmp_true
        or                    ::= expr jmp_false expr jmp_true expr
        or                    ::= expr_jt expr

        import_from ::= LOAD_CONST LOAD_CONST IMPORT_NAME importlist _come_froms POP_TOP

        ################################################################################
        # In many ways 3.0 is like 2.6. One similarity is there is no JUMP_IF_TRUE and
        # JUMP_IF_FALSE
        # The below rules in fact are the same or similar.

        jmp_true         ::= JUMP_IF_TRUE POP_TOP
        jmp_true_then    ::= JUMP_IF_TRUE _come_froms POP_TOP
        jmp_false        ::= JUMP_IF_FALSE _come_froms POP_TOP
        jmp_false_then   ::= JUMP_IF_FALSE POP_TOP

        # We don't have hacky THEN detection, so we do it
        # in the grammar below which is also somewhat hacky.

        stmt             ::= ifstmt30
        stmt             ::= ifnotstmt30
        ifstmt30         ::= testfalse_then _ifstmts_jump30
        ifnotstmt30      ::= testtrue_then  _ifstmts_jump30

        testfalse_then   ::= expr jmp_false_then
        testtrue_then    ::= expr jmp_true_then
        call_stmt        ::= expr COME_FROM
        _ifstmts_jump30  ::= c_stmts POP_TOP

        gen_comp_body    ::= expr YIELD_VALUE COME_FROM POP_TOP

        except_handler   ::= jmp_abs COME_FROM_EXCEPT except_stmts
                             COME_FROM POP_TOP END_FINALLY

        or               ::= expr jmp_true_then expr come_from_opt
        ret_or           ::= expr jmp_true_then expr come_from_opt
        ret_and          ::= expr jump_false expr come_from_opt

        ################################################################################
        for_block      ::= l_stmts_opt _come_froms POP_TOP JUMP_BACK

        except_handler ::= JUMP_FORWARD COME_FROM_EXCEPT except_stmts
                           POP_TOP END_FINALLY come_froms
        except_handler ::= jmp_abs COME_FROM_EXCEPT except_stmts
                           POP_TOP END_FINALLY

        return_if_stmt ::= return_expr RETURN_END_IF come_froms POP_TOP
        return_if_stmt ::= return_expr RETURN_VALUE come_froms POP_TOP

        and            ::= expr jmp_false_then expr come_from_opt

        whilestmt      ::= SETUP_LOOP testexpr l_stmts_opt come_from_opt
                           JUMP_BACK _come_froms POP_TOP POP_BLOCK COME_FROM_LOOP
        whilestmt      ::= SETUP_LOOP testexpr returns
                           POP_TOP POP_BLOCK COME_FROM_LOOP
        whilestmt      ::= SETUP_LOOP testexpr l_stmts_opt come_from_opt
                           come_froms POP_TOP POP_BLOCK COME_FROM_LOOP


        # compare_chained is like x <= y <= z
        compare_chained1  ::= expr DUP_TOP ROT_THREE COMPARE_OP
                              jmp_false compare_chained1 _come_froms
        compare_chained1  ::= expr DUP_TOP ROT_THREE COMPARE_OP
                              jmp_false compare_chained2 _come_froms
        compare_chained2 ::= expr COMPARE_OP RETURN_END_IF
        """


    def remove_rules_30(self):
        self.remove_rules("""

        # The were found using grammar coverage
        while1stmt     ::= SETUP_LOOP l_stmts COME_FROM JUMP_BACK COME_FROM_LOOP
        whileTruestmt  ::= SETUP_LOOP l_stmts_opt JUMP_BACK POP_BLOCK COME_FROM_LOOP
        whileelsestmt  ::= SETUP_LOOP testexpr l_stmts_opt JUMP_BACK POP_BLOCK else_suitel COME_FROM_LOOP
        whilestmt      ::= SETUP_LOOP testexpr l_stmts_opt JUMP_BACK POP_BLOCK COME_FROM_LOOP
        whilestmt      ::= SETUP_LOOP testexpr l_stmts_opt JUMP_BACK POP_BLOCK JUMP_BACK COME_FROM_LOOP
        whilestmt      ::= SETUP_LOOP testexpr returns POP_TOP POP_BLOCK COME_FROM_LOOP
        withasstmt     ::= expr SETUP_WITH store suite_stmts_opt POP_BLOCK LOAD_CONST COME_FROM_WITH WITH_CLEANUP END_FINALLY
        with           ::= expr SETUP_WITH POP_TOP suite_stmts_opt POP_BLOCK LOAD_CONST COME_FROM_WITH WITH_CLEANUP END_FINALLY

        # lc_body ::= LOAD_FAST expr LIST_APPEND
        # lc_body ::= LOAD_NAME expr LIST_APPEND
        # lc_body ::= expr LIST_APPEND
        # list_comp ::= BUILD_LIST_0 list_iter
        list_for ::= expr FOR_ITER store list_iter jb_or_c
        # list_if ::= expr jmp_false list_iter
        # list_if ::= expr jmp_false_then list_iter
        # list_if_not ::= expr jmp_true list_iter
        # list_iter ::= list_if JUMP_BACK
        # list_iter ::= list_if JUMP_BACK _come_froms POP_TOP
        # list_iter ::= list_if_not
        # load_closure ::= BUILD_TUPLE_0
        # load_genexpr ::= BUILD_TUPLE_1 LOAD_GENEXPR LOAD_STR

        ##########################################################################################

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

        ################################################################
        # No JUMP_IF_FALSE_OR_POP, JUMP_IF_TRUE_OR_POP,
        # POP_JUMP_IF_FALSE, or POP_JUMP_IF_TRUE

        jmp_false        ::= POP_JUMP_IF_FALSE
        jmp_true         ::= JUMP_IF_TRUE_OR_POP POP_TOP
        jmp_true         ::= POP_JUMP_IF_TRUE

        compare_chained1 ::= expr DUP_TOP ROT_THREE COMPARE_OP JUMP_IF_FALSE_OR_POP
                             compare_chained1 COME_FROM
        compare_chained1 ::= expr DUP_TOP ROT_THREE COMPARE_OP JUMP_IF_FALSE_OR_POP
                             compare_chained2 COME_FROM
        ret_or           ::= expr JUMP_IF_TRUE_OR_POP  return_expr_or_cond COME_FROM
        ret_and          ::= expr JUMP_IF_FALSE_OR_POP return_expr_or_cond COME_FROM
        if_exp_ret       ::= expr POP_JUMP_IF_FALSE expr RETURN_END_IF
                             COME_FROM return_expr_or_cond
        return_expr_or_cond ::= if_exp_ret
        or               ::= expr JUMP_IF_TRUE_OR_POP expr COME_FROM
        and              ::= expr JUMP_IF_TRUE_OR_POP expr COME_FROM
        and              ::= expr JUMP_IF_FALSE_OR_POP expr COME_FROM
        """)

    def customize_grammar_rules(self, tokens, customize):
        super(Python30Parser, self).customize_grammar_rules(tokens, customize)
        self.remove_rules_30()

        self.check_reduce["iflaststmtl"] = "AST"
        self.check_reduce['ifstmt'] = "AST"
        self.check_reduce["ifelsestmtc"] = "AST"
        self.check_reduce["ifelsestmt"] = "AST"
        # self.check_reduce["and"] = "stmt"
        return

    def reduce_is_invalid(self, rule, ast, tokens, first, last):
        invalid = super(Python30Parser,
                        self).reduce_is_invalid(rule, ast,
                                                tokens, first, last)
        if invalid:
            return invalid
        lhs = rule[0]
        if (
            lhs in ("iflaststmtl", "ifstmt",
                        "ifelsestmt", "ifelsestmtc") and ast[0] == "testexpr"
        ):
            testexpr = ast[0]
            if testexpr[0] == "testfalse":
                testfalse = testexpr[0]
                if lhs == "ifelsestmtc" and ast[2] == "jump_absolute_else":
                    jump_absolute_else = ast[2]
                    come_from = jump_absolute_else[2]
                    return come_from == "COME_FROM" and come_from.attr < tokens[first].offset
                    pass
                elif lhs in ("ifelsestmt", "ifelsestmtc") and ast[2] == "jump_cf_pop":
                    jump_cf_pop = ast[2]
                    come_froms = jump_cf_pop[0]
                    for come_from in come_froms:
                        if come_from.attr < tokens[first].offset:
                            return True
                    come_froms = jump_cf_pop[2]
                    if come_froms == "COME_FROM":
                        if come_froms.attr < tokens[first].offset:
                            return True
                        pass
                    elif come_froms == "_come_froms":
                        for come_from in come_froms:
                            if come_from.attr < tokens[first].offset:
                                return True

                    return False
                elif testfalse[1] == "jmp_false":
                    jmp_false = testfalse[1]
                    if last == len(tokens):
                        last -= 1
                    while (isinstance(tokens[first].offset, str) and first < last):
                        first += 1
                    if first == last:
                        return True
                    while (first < last and isinstance(tokens[last].offset, str)):
                        last -= 1
                    if rule[0] == "iflaststmtl":
                        return not (jmp_false[0].attr <= tokens[last].offset)
                    else:
                        jmp_false_target = jmp_false[0].attr
                        if tokens[first].offset > jmp_false_target:
                            return True
                        return (
                            (jmp_false_target > tokens[last].offset) and tokens[last] != "JUMP_FORWARD")
                    pass
                pass
            pass
        # elif lhs == "and":
        #     return tokens[last+1] == "JUMP_FORWARD"

    pass

class Python30ParserSingle(Python30Parser, PythonParserSingle):
    pass

if __name__ == '__main__':
    # Check grammar
    p = Python30Parser()
    p.remove_rules_30()
    p.check_grammar()
    from xdis.version_info import PYTHON_VERSION_TRIPLE, IS_PYPY
    if PYTHON_VERSION_TRIPLE[:2] == (3, 0):
        lhs, rhs, tokens, right_recursive, dup_rhs = p.check_sets()
        from uncompyle6.scanner import get_scanner
        s = get_scanner(PYTHON_VERSION_TRIPLE, IS_PYPY)
        opcode_set = set(s.opc.opname).union(set(
            """JUMP_BACK CONTINUE RETURN_END_IF COME_FROM
               LOAD_GENEXPR LOAD_ASSERT LOAD_SETCOMP LOAD_DICTCOMP LOAD_CLASSNAME
               LAMBDA_MARKER RETURN_LAST
            """.split()))
        ## FIXME: try this
        remain_tokens = set(tokens) - opcode_set
        import re
        remain_tokens = set([re.sub(r'_\d+$', '',  t) for t in remain_tokens])
        remain_tokens = set([re.sub('_CONT$', '', t) for t in remain_tokens])
        remain_tokens = set(remain_tokens) - opcode_set
        print(remain_tokens)
        import sys
        if len(sys.argv) > 1:
            from spark_parser.spark import rule2str
            for rule in sorted(p.rule2name.items()):
                print(rule2str(rule[0]))
