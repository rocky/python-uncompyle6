#  Copyright (c) 2016 Rocky Bernstein
#  Copyright (c) 2000-2002 by hartmut Goebel <hartmut@goebel.noris.de>

from spark_parser import DEFAULT_DEBUG as PARSER_DEFAULT_DEBUG
from uncompyle6.parser import PythonParserSingle
from uncompyle6.parsers.parse23 import Python23Parser

class Python22Parser(Python23Parser):

    def __init__(self, debug_parser=PARSER_DEFAULT_DEBUG):
        super(Python23Parser, self).__init__(debug_parser)
        self.customized = {}

    def p_misc22(self, args):
        '''
        _for ::= LOAD_CONST FOR_LOOP
        list_iter ::= list_if JUMP_FORWARD
                      COME_FROM POP_TOP COME_FROM
        list_for  ::= expr _for designator list_iter CONTINUE JUMP_FORWARD
                      COME_FROM POP_TOP COME_FROM
        '''

class Python22ParserSingle(Python23Parser, PythonParserSingle):
    pass

if __name__ == '__main__':
    # Check grammar
    p = Python22Parser()
    p.checkGrammar()
    p.dumpGrammar()

# local variables:
# tab-width: 4
