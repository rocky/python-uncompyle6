#  Copyright (c) 2016 Rocky Bernstein
"""
spark grammar differences over Python2.5 for Python 2.4.
"""

from uncompyle6.parser import PythonParserSingle
from spark_parser import DEFAULT_DEBUG as PARSER_DEFAULT_DEBUG
from uncompyle6.parsers.parse25 import Python25Parser

class Python24Parser(Python25Parser):
    def __init__(self, debug_parser=PARSER_DEFAULT_DEBUG):
        super(Python24Parser, self).__init__(debug_parser)
        self.customized = {}

    def p_misc24(self, args):
        '''
        # 2.5+ has two LOAD_CONSTs, one for the number '.'s in a relative import
        # keep positions similar to simplify semantic actions

        importstmt ::= filler LOAD_CONST import_as
        importfrom ::= filler LOAD_CONST IMPORT_NAME importlist2 POP_TOP
        importstar ::= filler LOAD_CONST IMPORT_NAME IMPORT_STAR

        importmultiple ::= filler LOAD_CONST import_as imports_cont
        import_cont    ::= filler LOAD_CONST import_as_cont

        # Python 2.5+ omits POP_TOP POP_BLOCK
        while1stmt ::= SETUP_LOOP l_stmts JUMP_BACK POP_TOP POP_BLOCK COME_FROM
        while1stmt ::= SETUP_LOOP l_stmts_opt JUMP_BACK POP_TOP POP_BLOCK COME_FROM

        # Python 2.5+:
        #  call_stmt ::= expr POP_TOP
        #  expr      ::= yield
        call_stmt ::= yield

        # Python 2.5+ adds POP_TOP at the end
        gen_comp_body ::= expr YIELD_VALUE
        '''

class Python24ParserSingle(Python24Parser, PythonParserSingle):
    pass

if __name__ == '__main__':
    # Check grammar
    p = Python24Parser()
    p.checkGrammar()
