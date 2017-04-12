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
        # Python 2.4 only adds something like the below for if 1:
        # However we will just treat it as a noop (which of course messes up
        # simple verify of bytecode.
        # See also below in reduce_is_invalid where we check that the JUMP_FORWARD
        # target matches the COME_FROM target
        stmt     ::= nop_stmt
        nop_stmt ::= JUMP_FORWARD POP_TOP COME_FROM


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

    def add_custom_rules(self, tokens, customize):
        super(Python24Parser, self).add_custom_rules(tokens, customize)
        if self.version == 2.4:
            self.check_reduce['nop_stmt'] = 'tokens'

    def reduce_is_invalid(self, rule, ast, tokens, first, last):
        invalid = super(Python24Parser,
                        self).reduce_is_invalid(rule, ast,
                                                tokens, first, last)
        if invalid:
            return invalid

        # FiXME: this code never gets called...
        lhs = rule[0]
        if lhs == 'nop_stmt':
            return not int(tokens[first].pattr) == tokens[last].offset

        return False

class Python24ParserSingle(Python24Parser, PythonParserSingle):
    pass

if __name__ == '__main__':
    # Check grammar
    p = Python24Parser()
    p.checkGrammar()
