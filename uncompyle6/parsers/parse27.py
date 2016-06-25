from uncompyle6.parser import PythonParserSingle
from spark_parser import DEFAULT_DEBUG as PARSER_DEFAULT_DEBUG
from uncompyle6.parsers.parse2 import Python2Parser

class Python27Parser(Python2Parser):

    def __init__(self, debug_parser=PARSER_DEFAULT_DEBUG):
        super(Python27Parser, self).__init__(debug_parser)
        self.customized = {}

    def p_try27(self, args):
        """
        try_middle   ::= JUMP_FORWARD COME_FROM except_stmts
                         END_FINALLY COME_FROM
        try_middle   ::= jmp_abs COME_FROM except_stmts
                         END_FINALLY

        except_cond1 ::= DUP_TOP expr COMPARE_OP
                         jmp_false POP_TOP POP_TOP POP_TOP

        except_cond2 ::= DUP_TOP expr COMPARE_OP
                         jmp_false POP_TOP designator POP_TOP
        """

    def p_misc27(self, args):
        """
        assert        ::= assert_expr jmp_true LOAD_ASSERT RAISE_VARARGS_1
        _ifstmts_jump ::= c_stmts_opt JUMP_FORWARD COME_FROM
        """

class Python26ParserSingle(Python2Parser, PythonParserSingle):
    pass

if __name__ == '__main__':
    # Check grammar
    p = Python27Parser()
    p.checkGrammar()
