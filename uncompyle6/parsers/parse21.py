#  Copyright (c) 2016-2017 Rocky Bernstein
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
        for         ::= SETUP_LOOP expr for_iter store
                        returns
                        POP_BLOCK COME_FROM
        for         ::= SETUP_LOOP expr for_iter store
                        l_stmts_opt _jump_back
                        POP_BLOCK COME_FROM

        expr        ::= conditional
        conditional ::= expr jmp_false expr JUMP_ABSOLUTE expr
        """

    def p_import21(self, args):
        '''
        alias ::= IMPORT_NAME_CONT store
        '''

class Python21ParserSingle(Python22Parser, PythonParserSingle):
    pass

if __name__ == '__main__':
    # Check grammar
    p = Python21Parser()
    p.check_grammar()
    p.dump_grammar()

# local variables:
# tab-width: 4
