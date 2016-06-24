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
        # FIXME: move parse2's corresponding rules to 2.7

        except_cond1 ::= DUP_TOP expr COMPARE_OP
                         JUMP_IF_FALSE POP_TOP POP_TOP POP_TOP POP_TOP
        except_cond2 ::= DUP_TOP expr COMPARE_OP
                         JUMP_IF_FALSE POP_TOP POP_TOP designator POP_TOP
        try_middle   ::= JUMP_FORWARD COME_FROM except_stmts
                         POP_TOP END_FINALLY COME_FROM
        """


    def p_comp26(self, args):
        '''
        list_iter  ::= list_if JUMP_BACK
	list_compr ::= BUILD_LIST_0 DUP_TOP
		       designator list_iter del_stmt
	lc_body    ::= LOAD_NAME expr LIST_APPEND


        '''

class Python26ParserSingle(Python2Parser, PythonParserSingle):
    pass

if __name__ == '__main__':
    # Check grammar
    p = Python26Parser()
    p.checkGrammar()
