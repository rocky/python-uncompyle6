#  Copyright (c) 2016 Rocky Bernstein
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
        except_cond1 ::= DUP_TOP expr COMPARE_OP
                         JUMP_IF_FALSE POP_TOP POP_TOP POP_TOP POP_TOP
        except_cond2 ::= DUP_TOP expr COMPARE_OP
                         JUMP_IF_FALSE POP_TOP POP_TOP designator POP_TOP

        # Might be a bug from when COME_FROM wasn't properly handled
        try_middle   ::= JUMP_FORWARD COME_FROM except_stmts
                         POP_TOP END_FINALLY come_froms

        try_middle   ::= JUMP_FORWARD COME_FROM except_stmts
                         END_FINALLY come_froms
        try_middle   ::= JUMP_FORWARD COME_FROM except_stmts
                         come_from_pop END_FINALLY come_froms
        try_middle   ::= JUMP_FORWARD COME_FROM except_stmts
                         END_FINALLY come_froms

        try_middle   ::= jmp_abs COME_FROM except_stmts
                         POP_TOP END_FINALLY

        try_middle   ::= jmp_abs COME_FROM except_stmts
                         come_from_pop END_FINALLY

        try_middle   ::= jmp_abs COME_FROM except_stmts
                         END_FINALLY

        trystmt      ::= SETUP_EXCEPT suite_stmts_opt come_from_pop
                         try_middle

        # Sometimes we don't put in COME_FROM to the next statement
        # like we do in 2.7. Perhaps we should?
        trystmt      ::= SETUP_EXCEPT suite_stmts_opt POP_BLOCK
                         try_middle

        except_suite ::= c_stmts_opt JUMP_FORWARD come_from_pop

        # Python 3 also has this.
        come_froms ::= come_froms COME_FROM
        come_froms ::= COME_FROM

        """

    # In contrast to Python 2.7, Python 2.6 has a lot of
    # POP_TOP's which come right after various jumps.
    # The COME_FROM instructions our scanner adds, here it is to assist
    # distinguishing the extraneous POP_TOPs from those that start
    # after one of these jumps
    def p_jumps26(self, args):
        """
        jmp_false    ::= JUMP_IF_FALSE
        jmp_true     ::= JUMP_IF_TRUE
        jmp_true     ::= JUMP_IF_TRUE POP_TOP
        jmp_false    ::= JUMP_IF_FALSE POP_TOP
        jf_pop       ::= JUMP_FORWARD come_from_pop
        jf_pop       ::= JUMP_ABSOLUTE come_from_pop
        jb_pop       ::= JUMP_BACK come_from_pop

        jb_cont      ::= JUMP_BACK
        jb_cont      ::= CONTINUE

        jb_cf_pop ::= JUMP_BACK come_froms POP_TOP
        ja_cf_pop ::= JUMP_ABSOLUTE come_from_pop
        jf_cf_pop ::= JUMP_FORWARD come_from_pop

        _ifstmts_jump ::= c_stmts_opt jf_pop COME_FROM
        _ifstmts_jump ::= c_stmts_opt JUMP_FORWARD COME_FROM come_from_pop
        _ifstmts_jump ::= c_stmts_opt JUMP_FORWARD come_froms POP_TOP COME_FROM

        # This is what happens after a jump where
        # we start a new block. For reasons I don't fully
        # understand, there is also a value on the top of the stack
        come_from_pop   ::=  COME_FROM POP_TOP
        """

    def p_stmt26(self, args):
        """
        assert ::= assert_expr jmp_true LOAD_ASSERT RAISE_VARARGS_1 come_from_pop
        assert2 ::= assert_expr jmp_true LOAD_ASSERT expr RAISE_VARARGS_2 come_from_pop

        ifelsestmt  ::= testexpr c_stmts_opt jf_pop else_suite COME_FROM
        ifelsestmt  ::= testexpr c_stmts_opt else_suitel come_froms POP_TOP

        # Semantic actions want else_suitel to be at index 2 or 3
        ifelsestmtl ::= testexpr c_stmts_opt jb_cf_pop else_suitel
        ifelsestmtc ::= testexpr c_stmts_opt ja_cf_pop else_suitec

        iflaststmt  ::= testexpr c_stmts_opt JUMP_ABSOLUTE come_froms POP_TOP

        # Semantic actions want suite_stmts_opt to be at index 3
        withstmt ::= expr setupwith SETUP_FINALLY suite_stmts_opt
                     POP_BLOCK LOAD_CONST COME_FROM WITH_CLEANUP END_FINALLY

        # This is truly weird. 2.7 does this (not including POP_TOP) with
        # opcode SETUP_WITH
        setupwith ::= DUP_TOP LOAD_ATTR ROT_TWO LOAD_ATTR CALL_FUNCTION_0 POP_TOP

        whilestmt ::= SETUP_LOOP testexpr l_stmts_opt jb_pop POP_BLOCK _come_from

        whilestmt ::= SETUP_LOOP testexpr l_stmts_opt jb_cf_pop POP_BLOCK COME_FROM

        return_if_stmt ::= ret_expr RETURN_END_IF come_from_pop

        iflaststmtl ::= testexpr c_stmts_opt JUMP_BACK come_from_pop
        iflaststmt  ::= testexpr c_stmts_opt JUMP_ABSOLUTE come_from_pop
        """

    def p_comp26(self, args):
        '''
        list_for ::= expr _for designator list_iter JUMP_BACK come_froms POP_TOP
        list_for ::= expr _for designator list_iter jb_cont

        list_iter  ::= list_if JUMP_BACK
	list_compr ::= BUILD_LIST_0 DUP_TOP
		       designator list_iter del_stmt
	list_compr ::= BUILD_LIST_0 DUP_TOP
		       designator list_iter JUMP_BACK del_stmt
	lc_body    ::= LOAD_NAME expr LIST_APPEND
	lc_body    ::= LOAD_FAST expr LIST_APPEND

        comp_for ::= SETUP_LOOP expr _for designator comp_iter JUMP_BACK POP_BLOCK COME_FROM


        # Make sure we keep indices the same as 2.7
        setup_loop_lf ::= SETUP_LOOP LOAD_FAST
        genexpr_func ::= setup_loop_lf FOR_ITER designator comp_iter JUMP_BACK POP_BLOCK COME_FROM
        genexpr_func ::= setup_loop_lf FOR_ITER designator comp_iter JUMP_BACK come_from_pop JUMP_BACK POP_BLOCK COME_FROM
        genexpr ::= LOAD_GENEXPR MAKE_FUNCTION_0 expr GET_ITER CALL_FUNCTION_1 COME_FROM

        '''

    def p_ret26(self, args):
        '''
        ret_and  ::= expr jmp_false ret_expr_or_cond COME_FROM
        ret_or   ::= expr jmp_true ret_expr_or_cond COME_FROM
        ret_cond ::= expr jmp_false expr RETURN_END_IF come_from_pop ret_expr_or_cond
        ret_cond ::= expr jmp_false expr ret_expr_or_cond
        ret_cond_not ::= expr jmp_true expr RETURN_END_IF come_from_pop ret_expr_or_cond

        # FIXME: split into Python 2.5
        ret_cond ::= expr jmp_false expr JUMP_RETURN come_from_pop ret_expr_or_cond
        ret_or   ::= expr jmp_true ret_expr_or_cond come_froms
        '''

    def p_except26(self, args):
        '''
        except_suite ::= c_stmts_opt jmp_abs come_from_pop
        '''

    def p_misc(self, args):
        '''
        conditional  ::= expr jmp_false expr jf_cf_pop expr come_from_opt
        '''

class Python26ParserSingle(Python2Parser, PythonParserSingle):
    pass

if __name__ == '__main__':
    # Check grammar
    p = Python26Parser()
    p.checkGrammar()
