#  Copyright (c) 2016-2018 Rocky Bernstein
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

        import           ::= filler LOAD_CONST alias
        import_from      ::= filler LOAD_CONST IMPORT_NAME importlist POP_TOP
        import_from_star ::= filler LOAD_CONST IMPORT_NAME IMPORT_STAR

        importmultiple ::= filler LOAD_CONST alias imports_cont
        import_cont    ::= filler LOAD_CONST alias

        # Handle "if true else: ..." in Python 2.4
        stmt            ::= iftrue_stmt24
        iftrue_stmt24   ::= _ifstmts_jump24 suite_stmts COME_FROM
        _ifstmts_jump24 ::= c_stmts_opt JUMP_FORWARD POP_TOP

        # Python 2.5+ omits POP_TOP POP_BLOCK
        while1stmt ::= SETUP_LOOP l_stmts_opt JUMP_BACK POP_TOP POP_BLOCK COME_FROM
        while1stmt ::= SETUP_LOOP l_stmts_opt JUMP_BACK POP_TOP POP_BLOCK

        # Python 2.5+:
        #  call_stmt ::= expr POP_TOP
        #  expr      ::= yield
        call_stmt ::= yield

        # Python 2.5+ adds POP_TOP at the end
        gen_comp_body ::= expr YIELD_VALUE

        # Python 2.4
        # Python 2.6, 2.7 and 3.3+ use kv3
        # Python 2.3- use kv
        kvlist ::= kvlist kv2
        kv2    ::= DUP_TOP expr expr ROT_THREE STORE_SUBSCR
        '''

    def customize_grammar_rules(self, tokens, customize):
        self.remove_rules("""
        gen_comp_body ::= expr YIELD_VALUE POP_TOP
        kvlist        ::= kvlist kv3
        while1stmt    ::= SETUP_LOOP l_stmts JUMP_BACK COME_FROM
        while1stmt    ::= SETUP_LOOP l_stmts_opt JUMP_BACK COME_FROM
        while1stmt    ::= SETUP_LOOP returns COME_FROM
        whilestmt     ::= SETUP_LOOP testexpr returns POP_BLOCK COME_FROM
        with_cleanup  ::= LOAD_FAST DELETE_FAST WITH_CLEANUP END_FINALLY
        with_cleanup  ::= LOAD_NAME DELETE_NAME WITH_CLEANUP END_FINALLY
        withasstmt    ::= expr setupwithas store suite_stmts_opt POP_BLOCK LOAD_CONST COME_FROM with_cleanup
        withstmt      ::= expr setupwith SETUP_FINALLY suite_stmts_opt POP_BLOCK LOAD_CONST COME_FROM with_cleanup
        stmt ::= withstmt
        stmt ::= withasstmt
        """)
        super(Python24Parser, self).customize_grammar_rules(tokens, customize)
        if self.version == 2.4:
            self.check_reduce['nop_stmt'] = 'tokens'

    def reduce_is_invalid(self, rule, ast, tokens, first, last):
        invalid = super(Python24Parser,
                        self).reduce_is_invalid(rule, ast,
                                                tokens, first, last)
        if invalid or tokens is None:
            return invalid

        lhs = rule[0]
        if lhs == 'nop_stmt':
            l = len(tokens)
            if 0 <= l < len(tokens):
                return not int(tokens[first].pattr) == tokens[last].offset
        elif lhs == 'try_except':
            if last == len(tokens):
                last -= 1
            if tokens[last] != 'COME_FROM' and tokens[last-1] == 'COME_FROM':
                last -= 1
            return (tokens[last] == 'COME_FROM'
                    and tokens[last-1] == 'END_FINALLY'
                    and tokens[last-2] == 'POP_TOP'
                    and tokens[last-3].kind != 'JUMP_FORWARD')

        return False

class Python24ParserSingle(Python24Parser, PythonParserSingle):
    pass

if __name__ == '__main__':
    # Check grammar
    p = Python24Parser()
    p.check_grammar()
