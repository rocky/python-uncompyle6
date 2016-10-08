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
        _for    ::= LOAD_CONST FOR_LOOP
        forstmt ::= SETUP_LOOP expr _for designator
                    return_stmts
                    POP_BLOCK COME_FROM
        forstmt ::= SETUP_LOOP expr _for designator
                    l_stmts_opt _jump_back
                    POP_BLOCK COME_FROM
        """

    def p_import21(self, args):
        '''
        # These are be relevant for only Python 2.0 and 2.1
	stmt ::= importstmt2
        stmt ::= importfrom2
	stmt ::= importstar
	stmt ::= import_as_cont
	stmt ::= import_as
        importfrom2    ::= LOAD_CONST IMPORT_NAME importlist2 POP_TOP
        importlist2    ::= importlist2 import_as
        importstmt2    ::= LOAD_CONST IMPORT_NAME designator
        importstmt2    ::= LOAD_CONST IMPORT_NAME IMPORT_FROM designator POP_TOP
        importstar     ::= LOAD_CONST LOAD_CONST IMPORT_NAME_CONT IMPORT_STAR
        importfrom     ::= LOAD_CONST LOAD_CONST IMPORT_NAME_CONT importlist2 POP_TOP
        import_as      ::= LOAD_CONST IMPORT_NAME LOAD_ATTR designator
        import_as      ::= LOAD_CONST IMPORT_NAME LOAD_ATTR LOAD_ATTR designator
        import_as      ::= LOAD_CONST IMPORT_NAME LOAD_ATTR LOAD_ATTR LOAD_ATTR designator
        import_as      ::= IMPORT_FROM designator
        import_as_cont ::= LOAD_CONST IMPORT_NAME_CONT designator
        import_as_cont ::= IMPORT_NAME_CONT load_attrs designator
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
