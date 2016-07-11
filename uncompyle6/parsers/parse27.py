#  Copyright (c) 2016 Rocky Bernstein
#  Copyright (c) 2005 by Dan Pascu <dan@windowmaker.org>
#  Copyright (c) 2000-2002 by hartmut Goebel <hartmut@goebel.noris.de>

from spark_parser import DEFAULT_DEBUG as PARSER_DEFAULT_DEBUG
from uncompyle6.parser import PythonParserSingle
from uncompyle6.parsers.parse2 import Python2Parser

class Python27Parser(Python2Parser):

    def __init__(self, debug_parser=PARSER_DEFAULT_DEBUG):
        super(Python27Parser, self).__init__(debug_parser)
        self.customized = {}

    def p_list_comprehension27(self, args):
        """
        list_for ::= expr _for designator list_iter JUMP_BACK
        """

    def p_try27(self, args):
        """
        try_middle   ::= JUMP_FORWARD COME_FROM except_stmts
                         END_FINALLY COME_FROM
        try_middle   ::= jmp_abs COME_FROM except_stmts
                         END_FINALLY

        tryelsestmt    ::= SETUP_EXCEPT suite_stmts_opt POP_BLOCK
                           try_middle else_suite COME_FROM

        except_cond1 ::= DUP_TOP expr COMPARE_OP
                         jmp_false POP_TOP POP_TOP POP_TOP

        except_cond2 ::= DUP_TOP expr COMPARE_OP
                         jmp_false POP_TOP designator POP_TOP
        """

    def p_jump27(self, args):
        """
        _ifstmts_jump ::= c_stmts_opt JUMP_FORWARD COME_FROM
        jmp_false ::= POP_JUMP_IF_FALSE
        jmp_true  ::= POP_JUMP_IF_TRUE
        bp_come_from    ::= POP_BLOCK COME_FROM
        """


    def p_stmt27(self, args):
        """
        assert        ::= assert_expr jmp_true LOAD_ASSERT RAISE_VARARGS_1
        assert2       ::= assert_expr jmp_true LOAD_ASSERT expr RAISE_VARARGS_2

        withstmt ::= expr SETUP_WITH POP_TOP suite_stmts_opt
                POP_BLOCK LOAD_CONST COME_FROM
                WITH_CLEANUP END_FINALLY

        withasstmt ::= expr SETUP_WITH designator suite_stmts_opt
                POP_BLOCK LOAD_CONST COME_FROM
                WITH_CLEANUP END_FINALLY

        # Common with 2.6
        while1stmt ::= SETUP_LOOP return_stmts bp_come_from
        while1stmt ::= SETUP_LOOP return_stmts COME_FROM
        """


class Python27ParserSingle(Python27Parser, PythonParserSingle):
    pass

if __name__ == '__main__':
    # Check grammar
    p = Python27Parser()
    p.checkGrammar()
