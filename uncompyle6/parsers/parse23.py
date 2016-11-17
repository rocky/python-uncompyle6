#  Copyright (c) 2016 Rocky Bernstein
#  Copyright (c) 2000-2002 by hartmut Goebel <hartmut@goebel.noris.de>
#  Copyright (c) 1999 John Aycock

from spark_parser import DEFAULT_DEBUG as PARSER_DEFAULT_DEBUG
from uncompyle6.parser import PythonParserSingle
from uncompyle6.parsers.parse24 import Python24Parser

class Python23Parser(Python24Parser):

    def __init__(self, debug_parser=PARSER_DEFAULT_DEBUG):
        super(Python24Parser, self).__init__(debug_parser)
        self.customized = {}

    def p_misc23(self, args):
        '''
        # Used to keep semantic positions the same across later versions
        # of Python
        _while1test ::= SETUP_LOOP JUMP_FORWARD JUMP_IF_FALSE POP_TOP COME_FROM

        while1stmt ::= _while1test l_stmts_opt JUMP_BACK
                       POP_TOP POP_BLOCK COME_FROM

        while1stmt ::= _while1test l_stmts_opt JUMP_BACK
                       COME_FROM POP_TOP POP_BLOCK COME_FROM

        list_compr ::= BUILD_LIST_0 DUP_TOP LOAD_ATTR designator list_iter del_stmt
        list_for   ::= expr _for designator list_iter JUMP_BACK come_froms POP_TOP JUMP_BACK

        lc_body ::= LOAD_NAME expr CALL_FUNCTION_1 POP_TOP
        lc_body ::= LOAD_FAST expr CALL_FUNCTION_1 POP_TOP
        lc_body ::= LOAD_NAME expr LIST_APPEND
        lc_body ::= LOAD_FAST expr LIST_APPEND
        '''

class Python23ParserSingle(Python23Parser, PythonParserSingle):
    pass

if __name__ == '__main__':
    # Check grammar
    p = Python23Parser()
    p.checkGrammar()
    p.dumpGrammar()

# local variables:
# tab-width: 4
