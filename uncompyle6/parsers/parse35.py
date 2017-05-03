#  Copyright (c) 2016 Rocky Bernstein
"""
spark grammar differences over Python 3.4 for Python 3.5.
"""
from __future__ import print_function

from uncompyle6.parser import PythonParserSingle
from spark_parser import DEFAULT_DEBUG as PARSER_DEFAULT_DEBUG
from uncompyle6.parsers.parse34 import Python34Parser

class Python35Parser(Python34Parser):

    def __init__(self, debug_parser=PARSER_DEFAULT_DEBUG):
        super(Python35Parser, self).__init__(debug_parser)
        self.customized = {}

    def p_35on(self, args):
        """
        # The number of canned instructions in new statements is mind boggling.
        # I'm sure by the time Python 4 comes around these will be turned
        # into special opcodes

        while1stmt     ::= SETUP_LOOP l_stmts COME_FROM JUMP_BACK
                           POP_BLOCK COME_FROM_LOOP
        while1stmt     ::= SETUP_LOOP l_stmts POP_BLOCK COME_FROM_LOOP
        while1elsestmt ::= SETUP_LOOP l_stmts JUMP_BACK
                           POP_BLOCK else_suite COME_FROM_LOOP

        # Python 3.5+ Await statement
        expr       ::= await_expr
        await_expr ::= expr GET_AWAITABLE LOAD_CONST YIELD_FROM

        stmt       ::= await_stmt
        await_stmt ::= await_expr POP_TOP

        expr       ::= unmap_dict
        expr       ::= unmapexpr

        unmap_dict ::= dictcomp BUILD_MAP_UNPACK

        unmap_dict ::= kv_lists BUILD_MAP_UNPACK
        kv_lists   ::= kv_list kv_lists
        kv_lists   ::= kv_list

        # Python 3.5+ has WITH_CLEANUP_START/FINISH

        withstmt    ::= expr
                        SETUP_WITH exprlist suite_stmts_opt
                        POP_BLOCK LOAD_CONST COME_FROM_WITH
                        WITH_CLEANUP_START WITH_CLEANUP_FINISH END_FINALLY

        withstmt   ::= expr
                       SETUP_WITH POP_TOP suite_stmts_opt
                       POP_BLOCK LOAD_CONST COME_FROM_WITH
                       WITH_CLEANUP_START WITH_CLEANUP_FINISH END_FINALLY

        withasstmt ::= expr
                       SETUP_WITH designator suite_stmts_opt
                       POP_BLOCK LOAD_CONST COME_FROM_WITH
                       WITH_CLEANUP_START WITH_CLEANUP_FINISH END_FINALLY


        # Python 3.5+ async additions

        stmt            ::= async_with_stmt
        async_with_stmt ::= expr
                            BEFORE_ASYNC_WITH GET_AWAITABLE LOAD_CONST YIELD_FROM
                            SETUP_ASYNC_WITH POP_TOP suite_stmts_opt
                            POP_BLOCK LOAD_CONST
                            WITH_CLEANUP_START
                            GET_AWAITABLE LOAD_CONST YIELD_FROM
                            WITH_CLEANUP_FINISH END_FINALLY

        stmt               ::= async_with_as_stmt
        async_with_as_stmt ::= expr
                               BEFORE_ASYNC_WITH GET_AWAITABLE LOAD_CONST YIELD_FROM
                               SETUP_ASYNC_WITH designator suite_stmts_opt
                               POP_BLOCK LOAD_CONST
                               WITH_CLEANUP_START
                               GET_AWAITABLE LOAD_CONST YIELD_FROM
                               WITH_CLEANUP_FINISH END_FINALLY

        stmt               ::= async_for_stmt
        async_for_stmt     ::= SETUP_LOOP expr
                               GET_AITER
                               LOAD_CONST YIELD_FROM SETUP_EXCEPT GET_ANEXT LOAD_CONST
                               YIELD_FROM
                               designator
                               POP_BLOCK jump_except COME_FROM_EXCEPT DUP_TOP
                               LOAD_GLOBAL COMPARE_OP POP_JUMP_IF_FALSE
                               POP_TOP POP_TOP POP_TOP POP_EXCEPT POP_BLOCK
                               JUMP_ABSOLUTE END_FINALLY COME_FROM
                               for_block POP_BLOCK JUMP_ABSOLUTE
                               opt_come_from_loop

        async_for_stmt     ::= SETUP_LOOP expr
                               GET_AITER
                               LOAD_CONST YIELD_FROM SETUP_EXCEPT GET_ANEXT LOAD_CONST
                               YIELD_FROM
                               designator
                               POP_BLOCK jump_except COME_FROM_EXCEPT DUP_TOP
                               LOAD_GLOBAL COMPARE_OP POP_JUMP_IF_FALSE
                               POP_TOP POP_TOP POP_TOP POP_EXCEPT POP_BLOCK
                               JUMP_ABSOLUTE END_FINALLY JUMP_BACK
                               passstmt POP_BLOCK JUMP_ABSOLUTE
                               opt_come_from_loop

        stmt               ::= async_forelse_stmt
        async_forelse_stmt ::= SETUP_LOOP expr
                               GET_AITER
                               LOAD_CONST YIELD_FROM SETUP_EXCEPT GET_ANEXT LOAD_CONST
                               YIELD_FROM
                               designator
                               POP_BLOCK JUMP_FORWARD COME_FROM_EXCEPT DUP_TOP
                               LOAD_GLOBAL COMPARE_OP POP_JUMP_IF_FALSE
                               POP_TOP POP_TOP POP_TOP POP_EXCEPT POP_BLOCK
                               JUMP_ABSOLUTE END_FINALLY COME_FROM
                               for_block POP_BLOCK JUMP_ABSOLUTE
                               else_suite COME_FROM_LOOP


        inplace_op ::= INPLACE_MATRIX_MULTIPLY
        binary_op  ::= BINARY_MATRIX_MULTIPLY

        # Python 3.5+ does jump optimization
        # In <.3.5 the below is a JUMP_FORWARD to a JUMP_ABSOLUTE.

        return_if_stmt ::= ret_expr RETURN_END_IF POP_BLOCK

        ifelsestmtc ::= testexpr c_stmts_opt JUMP_FORWARD else_suitec
        ifelsestmtc ::= testexpr c_stmts_opt jf_else else_suitec

        # ifstmt ::= testexpr c_stmts_opt

        iflaststmt ::= testexpr c_stmts_opt JUMP_FORWARD

        # Python 3.3+ also has yield from. 3.5 does it
        # differently than 3.3, 3.4

        yield_from ::= expr GET_YIELD_FROM_ITER LOAD_CONST YIELD_FROM
        """

    def add_custom_rules(self, tokens, customize):
        super(Python35Parser, self).add_custom_rules(tokens, customize)
        for i, token in enumerate(tokens):
            opname = token.type
            if opname == 'BUILD_MAP_UNPACK_WITH_CALL':
                nargs = token.attr % 256
                map_unpack_n = "map_unpack_%s" % nargs
                rule = map_unpack_n + ' ::= ' + 'expr ' * (nargs)
                self.add_unique_rule(rule, opname, token.attr, customize)
                rule = "unmapexpr ::=  %s %s" % (map_unpack_n, opname)
                self.add_unique_rule(rule, opname, token.attr, customize)
                call_token = tokens[i+1]
                if self.version == 3.5:
                    rule = 'call_function ::= expr unmapexpr ' + call_token.type
                    self.add_unique_rule(rule, opname, token.attr, customize)
                pass
            pass
        return

class Python35ParserSingle(Python35Parser, PythonParserSingle):
    pass

if __name__ == '__main__':
    # Check grammar
    p = Python35Parser()
    p.checkGrammar()
    from uncompyle6 import PYTHON_VERSION, IS_PYPY
    if PYTHON_VERSION == 3.5:
        lhs, rhs, tokens, right_recursive = p.checkSets()
        from uncompyle6.scanner import get_scanner
        s = get_scanner(PYTHON_VERSION, IS_PYPY)
        opcode_set = set(s.opc.opname).union(set(
            """JUMP_BACK CONTINUE RETURN_END_IF COME_FROM
               LOAD_GENEXPR LOAD_ASSERT LOAD_SETCOMP LOAD_DICTCOMP LOAD_CLASSNAME
               LAMBDA_MARKER RETURN_LAST
            """.split()))
        remain_tokens = set(tokens) - opcode_set
        import re
        remain_tokens = set([re.sub('_\d+$', '', t) for t in remain_tokens])
        remain_tokens = set([re.sub('_CONT$', '', t) for t in remain_tokens])
        remain_tokens = set(remain_tokens) - opcode_set
        print(remain_tokens)
        # print(sorted(p.rule2name.items()))
