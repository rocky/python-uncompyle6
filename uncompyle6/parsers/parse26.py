#  Copyright (c) 2017 Rocky Bernstein
"""
spark grammar differences over Python2 for Python 2.6.
"""

from uncompyle6.parser import PythonParserSingle
from spark_parser import DEFAULT_DEBUG as PARSER_DEFAULT_DEBUG
from uncompyle6.parsers.parse2 import Python2Parser

class Python26Parser(Python2Parser):

    def __init__(self, debug_parser=PARSER_DEFAULT_DEBUG):
        super(Python26Parser, self).__init__(debug_parser)
        self.customized = {}

    def p_try_except26(self, args):
        """
        except_stmt  ::= except_cond3 except_suite
        except_cond1 ::= DUP_TOP expr COMPARE_OP
                         JUMP_IF_FALSE POP_TOP POP_TOP POP_TOP POP_TOP
        except_cond3 ::= DUP_TOP expr COMPARE_OP
                         JUMP_IF_FALSE POP_TOP POP_TOP designator POP_TOP

        try_middle   ::= JUMP_FORWARD COME_FROM except_stmts
                         come_from_pop END_FINALLY come_froms

        try_middle   ::= JUMP_FORWARD COME_FROM except_stmts END_FINALLY
                         come_froms

        try_middle   ::= jmp_abs COME_FROM except_stmts
                         POP_TOP END_FINALLY

        try_middle   ::= jmp_abs COME_FROM except_stmts
                         END_FINALLY JUMP_FORWARD

        # Sometimes we don't put in COME_FROM to the next statement
        # like we do in 2.7. Perhaps we should?
        trystmt      ::= SETUP_EXCEPT suite_stmts_opt POP_BLOCK
                         try_middle

        tryelsestmt    ::= SETUP_EXCEPT suite_stmts_opt POP_BLOCK
                           try_middle else_suite COME_FROM

        _ifstmts_jump ::= c_stmts_opt JUMP_FORWARD COME_FROM POP_TOP

        except_suite ::= c_stmts_opt JUMP_FORWARD come_from_pop
        except_suite ::= c_stmts_opt JUMP_FORWARD POP_TOP
        except_suite ::= c_stmts_opt jmp_abs come_from_pop

        # Python 3 also has this.
        come_froms ::= come_froms COME_FROM
        come_froms ::= COME_FROM

        # This is what happens after a jump where
        # we start a new block. For reasons I don't fully
        # understand, there is also a value on the top of the stack
        come_from_pop   ::=  COME_FROM POP_TOP
        come_froms_pop ::= come_froms POP_TOP

        """

    # In contrast to Python 2.7, Python 2.6 has a lot of
    # POP_TOP's which come right after various jumps.
    # The COME_FROM instructions our scanner adds, here it is to assist
    # distinguishing the extraneous POP_TOPs from those that start
    # after one of these jumps
    def p_jumps26(self, args):
        """

        # The are the equivalents of Python 2.7+'s
        # POP_JUMP_IF_TRUE and POP_JUMP_IF_FALSE
        jmp_true     ::= JUMP_IF_TRUE POP_TOP
        jmp_false    ::= JUMP_IF_FALSE POP_TOP

        jf_pop       ::= JUMP_FORWARD POP_TOP
        jf_pop       ::= JUMP_ABSOLUTE POP_TOP
        jb_pop       ::= JUMP_BACK POP_TOP

        jb_cont      ::= JUMP_BACK
        jb_cont      ::= CONTINUE

        jb_cf_pop ::= JUMP_BACK come_froms POP_TOP
        jb_cf_pop ::= JUMP_BACK POP_TOP
        ja_cf_pop ::= JUMP_ABSOLUTE come_froms POP_TOP
        jf_cf_pop ::= JUMP_FORWARD come_froms POP_TOP

        bp_come_from    ::= POP_BLOCK COME_FROM
        jb_bp_come_from ::= JUMP_BACK bp_come_from

        _ifstmts_jump ::= c_stmts_opt jf_pop COME_FROM
        _ifstmts_jump ::= c_stmts_opt JUMP_FORWARD COME_FROM POP_TOP
        _ifstmts_jump ::= c_stmts_opt JUMP_FORWARD come_froms POP_TOP COME_FROM

        # This is what happens after a jump where
        # we start a new block. For reasons I don't fully
        # understand, there is also a value on the top of the stack
        come_froms_pop  ::=  come_froms POP_TOP

        """

    def p_stmt26(self, args):
        """
        # We use filler as a placeholder to keep nonterminal positions
        # the same across different grammars so that the same semantic actions
        # can be used
        filler ::=

        assert ::= assert_expr jmp_true LOAD_ASSERT RAISE_VARARGS_1 come_froms_pop
        assert2 ::= assert_expr jmp_true LOAD_ASSERT expr RAISE_VARARGS_2 come_froms_pop

        break_stmt ::= BREAK_LOOP JUMP_BACK

        # Semantic actions want else_suitel to be at index 3
        ifelsestmtl ::= testexpr c_stmts_opt jb_cf_pop else_suitel
        ifelsestmtc ::= testexpr c_stmts_opt ja_cf_pop else_suitec

        # Semantic actions want suite_stmts_opt to be at index 3
        withstmt ::= expr setupwith SETUP_FINALLY suite_stmts_opt
                     POP_BLOCK LOAD_CONST COME_FROM WITH_CLEANUP END_FINALLY

        # Semantic actions want designator to be at index 2
        # Rule is possibly 2.6 only
        withasstmt ::= expr setupwithas designator suite_stmts_opt
                       POP_BLOCK LOAD_CONST COME_FROM WITH_CLEANUP END_FINALLY

        # This is truly weird. 2.7 does this (not including POP_TOP) with
        # opcode SETUP_WITH
        setupwith ::= DUP_TOP LOAD_ATTR ROT_TWO LOAD_ATTR CALL_FUNCTION_0 POP_TOP

        # Possibly 2.6 only
        setupwithas ::= DUP_TOP LOAD_ATTR ROT_TWO LOAD_ATTR CALL_FUNCTION_0 setup_finally

        setup_finally ::= STORE_FAST SETUP_FINALLY LOAD_FAST DELETE_FAST
        setup_finally ::= STORE_NAME SETUP_FINALLY LOAD_NAME DELETE_NAME


        whilestmt ::= SETUP_LOOP testexpr l_stmts_opt jb_pop POP_BLOCK _come_from
        whilestmt ::= SETUP_LOOP testexpr l_stmts_opt jb_cf_pop bp_come_from
        whilestmt ::= SETUP_LOOP testexpr return_stmts come_froms POP_TOP bp_come_from

        whileelsestmt ::= SETUP_LOOP testexpr l_stmts_opt jb_pop POP_BLOCK
                          else_suite COME_FROM

        return_stmt ::= ret_expr RETURN_END_IF POP_TOP
        return_stmt ::= ret_expr RETURN_VALUE POP_TOP
        return_if_stmt ::= ret_expr RETURN_END_IF POP_TOP

        iflaststmtl ::= testexpr c_stmts_opt JUMP_BACK come_from_pop
        iflaststmt  ::= testexpr c_stmts_opt JUMP_ABSOLUTE come_from_pop

        lastc_stmt ::= iflaststmt COME_FROM

        while1stmt ::= SETUP_LOOP l_stmts_opt JUMP_BACK COME_FROM

        ifstmt         ::= testexpr_then _ifstmts_jump

        # Semantic actions want the else to be at position 3
        ifelsestmt     ::= testexpr      c_stmts_opt jf_cf_pop else_suite come_froms
        ifelsestmt     ::= testexpr_then c_stmts_opt jf_cf_pop else_suite come_froms
        ifelsestmt     ::= testexpr_then c_stmts_opt filler else_suitel come_froms POP_TOP

        # Semantic actions want else_suitel to be at index 3
        ifelsestmtl    ::= testexpr_then c_stmts_opt jb_cf_pop else_suitel
        ifelsestmtc    ::= testexpr_then c_stmts_opt ja_cf_pop else_suitec

        iflaststmt     ::= testexpr_then c_stmts_opt JUMP_ABSOLUTE come_froms POP_TOP
        iflaststmt     ::= testexpr      c_stmts_opt JUMP_ABSOLUTE come_froms POP_TOP

        testexpr_then  ::= testtrue_then
        testexpr_then  ::= testfalse_then
        testtrue_then  ::= expr jmp_true_then
        testfalse_then ::= expr jmp_false_then

        jmp_false_then ::= JUMP_IF_FALSE THEN POP_TOP
        jmp_true_then  ::= JUMP_IF_TRUE THEN POP_TOP

        # Common with 2.7
        while1stmt ::= SETUP_LOOP return_stmts bp_come_from
        while1stmt ::= SETUP_LOOP return_stmts COME_FROM
        """

    def p_comp26(self, args):
        '''
        list_for ::= expr _for designator list_iter JUMP_BACK come_froms POP_TOP

        # The JUMP FORWARD below jumps to the JUMP BACK. It seems to happen
        # in rare cases that may have to with length of code
        list_for ::= expr _for designator list_iter JUMP_FORWARD come_froms POP_TOP
                     COME_FROM JUMP_BACK

        list_for ::= expr _for designator list_iter jb_cont

        list_iter  ::= list_if JUMP_BACK
        list_iter  ::= list_if JUMP_BACK COME_FROM POP_TOP
        list_compr ::= BUILD_LIST_0 DUP_TOP
                       designator list_iter del_stmt
        list_compr ::= BUILD_LIST_0 DUP_TOP
	               designator list_iter JUMP_BACK del_stmt
        lc_body    ::= LOAD_NAME expr LIST_APPEND
	lc_body    ::= LOAD_FAST expr LIST_APPEND

        comp_for ::= SETUP_LOOP expr _for designator comp_iter jb_bp_come_from

        comp_body ::= gen_comp_body

        for_block ::= l_stmts_opt _come_from POP_TOP JUMP_BACK

        # Make sure we keep indices the same as 2.7
        setup_loop_lf ::= SETUP_LOOP LOAD_FAST
        genexpr_func ::= setup_loop_lf FOR_ITER designator comp_iter jb_bp_come_from
        genexpr_func ::= setup_loop_lf FOR_ITER designator comp_iter JUMP_BACK come_from_pop
                         jb_bp_come_from
        genexpr ::= LOAD_GENEXPR MAKE_FUNCTION_0 expr GET_ITER CALL_FUNCTION_1 COME_FROM
        list_if ::= list_if ::= expr jmp_false_then list_iter
        '''

    def p_ret26(self, args):
        '''
        ret_and      ::= expr jmp_false ret_expr_or_cond COME_FROM
        ret_or       ::= expr jmp_true ret_expr_or_cond COME_FROM
        ret_cond     ::= expr jmp_false_then expr RETURN_END_IF POP_TOP ret_expr_or_cond
        ret_cond     ::= expr jmp_false_then expr ret_expr_or_cond
        ret_cond_not ::= expr jmp_true_then  expr RETURN_END_IF POP_TOP ret_expr_or_cond

        return_if_stmt ::= ret_expr RETURN_END_IF POP_TOP
        return_stmt ::= ret_expr RETURN_VALUE POP_TOP

        # FIXME: split into Python 2.5
        ret_or   ::= expr jmp_true ret_expr_or_cond come_froms
        '''

    def p_except26(self, args):
        """
        except_suite ::= c_stmts_opt jmp_abs POP_TOP
        """

    def p_misc26(self, args):
        """
        conditional  ::= expr jmp_false expr jf_cf_pop expr come_from_opt
        and  ::= expr JUMP_IF_FALSE POP_TOP expr JUMP_IF_FALSE POP_TOP
        cmp_list ::= expr cmp_list1 ROT_TWO COME_FROM POP_TOP _come_from

        conditional_lambda ::= expr jmp_false_then return_if_stmt return_stmt LAMBDA_MARKER
        """

    def add_custom_rules(self, tokens, customize):
        super(Python26Parser, self).add_custom_rules(tokens, customize)
        self.check_reduce['and'] = 'AST'

    def reduce_is_invalid(self, rule, ast, tokens, first, last):
        invalid = super(Python26Parser,
                        self).reduce_is_invalid(rule, ast,
                                                tokens, first, last)
        if invalid:
            return invalid
        if rule == ('and', ('expr', 'jmp_false', 'expr', '\\e_come_from_opt')):
            # Test that jmp_false jumps to the end of "and"
            # or that it jumps to the same place as the end of "and"
            jmp_false = ast[1][0]
            jmp_target = jmp_false.offset + jmp_false.attr + 3
            return not (jmp_target == tokens[last].offset or
                        tokens[last].pattr == jmp_false.pattr)
        return False
class Python26ParserSingle(Python2Parser, PythonParserSingle):
    pass

if __name__ == '__main__':
    # Check grammar
    p = Python26Parser()
    p.checkGrammar()
    from uncompyle6 import PYTHON_VERSION, IS_PYPY
    if PYTHON_VERSION == 2.6:
        lhs, rhs, tokens, right_recursive = p.checkSets()
        from uncompyle6.scanner import get_scanner
        s = get_scanner(PYTHON_VERSION, IS_PYPY)
        opcode_set = set(s.opc.opname).union(set(
            """JUMP_BACK CONTINUE RETURN_END_IF COME_FROM
               LOAD_GENEXPR LOAD_ASSERT LOAD_SETCOMP LOAD_DICTCOMP
               LAMBDA_MARKER RETURN_LAST
            """.split()))
        remain_tokens = set(tokens) - opcode_set
        import re
        remain_tokens = set([re.sub('_\d+$', '', t) for t in remain_tokens])
        remain_tokens = set([re.sub('_CONT$', '', t) for t in remain_tokens])
        remain_tokens = set(remain_tokens) - opcode_set
        print(remain_tokens)
        # print(sorted(p.rule2name.items()))
