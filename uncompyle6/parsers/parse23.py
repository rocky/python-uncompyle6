#  Copyright (c) 2016-2018, 2020 Rocky Bernstein
#  Copyright (c) 2000-2002 by hartmut Goebel <hartmut@goebel.noris.de>
#  Copyright (c) 1999 John Aycock

from spark_parser import DEFAULT_DEBUG as PARSER_DEFAULT_DEBUG
from uncompyle6.parser import PythonParserSingle
from uncompyle6.parsers.parse24 import Python24Parser

class Python23Parser(Python24Parser):

    def __init__(self, debug_parser=PARSER_DEFAULT_DEBUG):
        super(Python23Parser, self).__init__(debug_parser)
        self.customized = {}

    def p_misc23(self, args):
        '''
        # Python 2.4 only adds something like the below for if 1:
        # However we will just treat it as a noop (which of course messes up
        # simple verify of bytecode.
        # See also below in reduce_is_invalid where we check that the JUMP_FORWARD
        # target matches the COME_FROM target
        stmt     ::= if1_stmt
        if1_stmt ::= JUMP_FORWARD JUMP_IF_FALSE THEN POP_TOP COME_FROM
                     stmts
                     JUMP_FORWARD COME_FROM POP_TOP COME_FROM


        # Used to keep semantic positions the same across later versions
        # of Python
        _while1test ::= SETUP_LOOP JUMP_FORWARD JUMP_IF_FALSE POP_TOP COME_FROM

        while1stmt ::= _while1test l_stmts_opt JUMP_BACK
                       POP_TOP POP_BLOCK COME_FROM

        while1stmt ::= _while1test l_stmts_opt JUMP_BACK COME_FROM
                       POP_TOP POP_BLOCK COME_FROM

        # Python 2.3
        # The following has no "JUMP_BACK" after l_stmts because
        # l_stmts ends in a "break", "return", or "continue"
        while1stmt ::= _while1test l_stmts
                       POP_TOP POP_BLOCK

        # The following has a "COME_FROM" at the end which comes from
        # a "break" inside "l_stmts".
        while1stmt ::= _while1test l_stmts COME_FROM JUMP_BACK
                       POP_TOP POP_BLOCK COME_FROM
        while1stmt ::= _while1test l_stmts JUMP_BACK
                       POP_TOP POP_BLOCK

        list_comp  ::= BUILD_LIST_0 DUP_TOP LOAD_ATTR store list_iter delete
        list_for   ::= expr for_iter store list_iter JUMP_BACK come_froms POP_TOP JUMP_BACK

        lc_body ::= LOAD_NAME expr CALL_FUNCTION_1 POP_TOP
        lc_body ::= LOAD_FAST expr CALL_FUNCTION_1 POP_TOP
        lc_body ::= LOAD_NAME expr LIST_APPEND
        lc_body ::= LOAD_FAST expr LIST_APPEND

        # "and" where the first part of the and is true,
        # so there is only the 2nd part to evaluate
        expr ::= and2
        and2 ::= _jump jmp_false COME_FROM expr COME_FROM

        alias       ::= IMPORT_NAME attributes store
        if_exp      ::= expr jmp_false expr JUMP_FORWARD expr COME_FROM
        '''

    def customize_grammar_rules(self, tokens, customize):
        super(Python23Parser, self).customize_grammar_rules(tokens, customize)

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

class Python23ParserSingle(Python23Parser, PythonParserSingle):
    pass

if __name__ == '__main__':
    # Check grammar
    p = Python23Parser()
    p.check_grammar()
    p.dump_grammar()

# local variables:
# tab-width: 4
