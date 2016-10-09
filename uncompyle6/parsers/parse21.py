#  Copyright (c) 2016 Rocky Bernstein
#  Copyright (c) 2000-2002 by hartmut Goebel <hartmut@goebel.noris.de>

from spark_parser import DEFAULT_DEBUG as PARSER_DEFAULT_DEBUG
from uncompyle6.parser import PythonParserSingle
from uncompyle6.parsers.parse22 import Python22Parser

class Python21Parser(Python22Parser):

    def __init__(self, debug_parser=PARSER_DEFAULT_DEBUG):
        super(Python22Parser, self).__init__(debug_parser)
        self.customized = {}

    def p_forstmt21(self, args):
        """
        _for      ::= LOAD_CONST FOR_LOOP
        forstmt   ::= SETUP_LOOP expr _for designator
                      return_stmts
                      POP_BLOCK COME_FROM
        forstmt   ::= SETUP_LOOP expr _for designator
                      l_stmts_opt _jump_back
                      POP_BLOCK COME_FROM
        """

    def p_import21(self, args):
        '''
        import_as ::= IMPORT_NAME_CONT designator
        '''

class Python21ParserSingle(Python22Parser, PythonParserSingle):
    pass

if __name__ == '__main__':
    # Check grammar
    p = Python21Parser()
    p.checkGrammar()
    p.dumpGrammar()

# local variables:
# tab-width: 4
