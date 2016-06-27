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
        try_middle   ::= JUMP_FORWARD COME_FROM except_stmts
                         POP_TOP END_FINALLY come_froms
        try_middle   ::= JUMP_FORWARD COME_FROM except_stmts
                         COME_FROM POP_TOP END_FINALLY come_froms
        try_middle   ::= JUMP_FORWARD COME_FROM except_stmts
                         END_FINALLY come_froms
        try_middle   ::= jmp_abs COME_FROM except_stmts
                         POP_TOP END_FINALLY

        trystmt      ::= SETUP_EXCEPT suite_stmts_opt POP_BLOCK
                         try_middle

        except_suite ::= c_stmts_opt JUMP_FORWARD POP_TOP

        # Python 3 also has this.
        come_froms ::= come_froms COME_FROM
        come_froms ::= COME_FROM

        """

    def p_whilestmt(self, args):
        """
        whilestmt ::= SETUP_LOOP
                testexpr
                l_stmts_opt jb_pop
                POP_BLOCK _come_from

        """

    def p_misc26(self, args):
        """
        jmp_true     ::=  JUMP_IF_TRUE POP_TOP
        jmp_false    ::=  JUMP_IF_FALSE POP_TOP
        jf_pop       ::=  JUMP_FORWARD COME_FROM POP_TOP
        jb_pop       ::=  JUMP_BACK COME_FROM POP_TOP

        _ifstmts_jump ::= c_stmts_opt jf_pop COME_FROM
        """

    def p_stmt26(self, args):
        """
        assert ::= assert_expr jmp_true LOAD_ASSERT RAISE_VARARGS_1 POP_TOP
        ifelsestmt ::= testexpr c_stmts_opt jf_pop else_suite COME_FROM
        """

    def p_comp26(self, args):
        '''
        list_for ::= expr _for designator list_iter JUMP_BACK come_froms POP_TOP

        list_iter  ::= list_if JUMP_BACK
	list_compr ::= BUILD_LIST_0 DUP_TOP
		       designator list_iter del_stmt
	list_compr ::= BUILD_LIST_0 DUP_TOP
		       designator list_iter JUMP_BACK del_stmt
	lc_body    ::= LOAD_NAME expr LIST_APPEND
	lc_body    ::= LOAD_FAST expr LIST_APPEND
        '''

    def p_ret26(self, args):
        '''
        ret_cond ::= expr jmp_false expr RETURN_END_IF COME_FROM POP_TOP ret_expr_or_cond
        ret_or ::= expr jmp_true ret_expr_or_cond COME_FROM
        '''


class Python26ParserSingle(Python2Parser, PythonParserSingle):
    pass

if __name__ == '__main__':
    # Check grammar
    p = Python26Parser()
    p.checkGrammar()
