#  Copyright (c) 2016-2017 Rocky Bernstein
"""
spark grammar differences over Python 3.4 for Python 3.5.
"""

from uncompyle6.parser import PythonParserSingle, nop_func
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
        whilestmt      ::= SETUP_LOOP testexpr returns POP_BLOCK COME_FROM_LOOP

        # The following rule is for Python 3.5+ where we can have stuff like
        # while ..
        #     if
        #     ...
        # the end of the if will jump back to the loop and there will be a COME_FROM
        # after the jump
        l_stmts ::= lastl_stmt COME_FROM l_stmts

        # Python 3.5+ Await statement
        expr       ::= await_expr
        await_expr ::= expr GET_AWAITABLE LOAD_CONST YIELD_FROM

        stmt       ::= await_stmt
        await_stmt ::= await_expr POP_TOP

        # Python 3.5+ has WITH_CLEANUP_START/FINISH

        withstmt   ::= expr
                       SETUP_WITH POP_TOP suite_stmts_opt
                       POP_BLOCK LOAD_CONST COME_FROM_WITH
                       WITH_CLEANUP_START WITH_CLEANUP_FINISH END_FINALLY

        withasstmt ::= expr
                       SETUP_WITH store suite_stmts_opt
                       POP_BLOCK LOAD_CONST COME_FROM_WITH
                       WITH_CLEANUP_START WITH_CLEANUP_FINISH END_FINALLY

        # Python 3.5+ async additions
        stmt               ::= async_for_stmt
        async_for_stmt     ::= SETUP_LOOP expr
                               GET_AITER
                               LOAD_CONST YIELD_FROM SETUP_EXCEPT GET_ANEXT LOAD_CONST
                               YIELD_FROM
                               store
                               POP_BLOCK jump_except COME_FROM_EXCEPT DUP_TOP
                               LOAD_GLOBAL COMPARE_OP POP_JUMP_IF_FALSE
                               POP_TOP POP_TOP POP_TOP POP_EXCEPT POP_BLOCK
                               JUMP_ABSOLUTE END_FINALLY COME_FROM
                               for_block POP_BLOCK JUMP_ABSOLUTE
                               COME_FROM_LOOP

        async_for_stmt     ::= SETUP_LOOP expr
                               GET_AITER
                               LOAD_CONST YIELD_FROM SETUP_EXCEPT GET_ANEXT LOAD_CONST
                               YIELD_FROM
                               store
                               POP_BLOCK jump_except COME_FROM_EXCEPT DUP_TOP
                               LOAD_GLOBAL COMPARE_OP POP_JUMP_IF_FALSE
                               POP_TOP POP_TOP POP_TOP POP_EXCEPT POP_BLOCK
                               JUMP_ABSOLUTE END_FINALLY JUMP_BACK
                               pass POP_BLOCK JUMP_ABSOLUTE
                               COME_FROM_LOOP

        stmt               ::= async_forelse_stmt
        async_forelse_stmt ::= SETUP_LOOP expr
                               GET_AITER
                               LOAD_CONST YIELD_FROM SETUP_EXCEPT GET_ANEXT LOAD_CONST
                               YIELD_FROM
                               store
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

        # ifstmt ::= testexpr c_stmts_opt

        iflaststmt ::= testexpr c_stmts_opt JUMP_FORWARD

        # Python 3.3+ also has yield from. 3.5 does it
        # differently than 3.3, 3.4

        yield_from ::= expr GET_YIELD_FROM_ITER LOAD_CONST YIELD_FROM
        """

    def customize_grammar_rules(self, tokens, customize):
        self.remove_rules("""
          yield_from ::= expr GET_ITER LOAD_CONST YIELD_FROM
          yield_from ::= expr expr YIELD_FROM
          withstmt   ::= expr SETUP_WITH POP_TOP suite_stmts_opt
                         POP_BLOCK LOAD_CONST COME_FROM_WITH
                         WITH_CLEANUP END_FINALLY
          withasstmt ::= expr SETUP_WITH store suite_stmts_opt
                         POP_BLOCK LOAD_CONST COME_FROM_WITH
                         WITH_CLEANUP END_FINALLY
        """)
        super(Python35Parser, self).customize_grammar_rules(tokens, customize)
        for i, token in enumerate(tokens):
            opname = token.kind
            if opname == 'BUILD_MAP_UNPACK_WITH_CALL':
                self.addRule("expr ::= unmapexpr", nop_func)
                nargs = token.attr % 256
                map_unpack_n = "map_unpack_%s" % nargs
                rule = map_unpack_n + ' ::= ' + 'expr ' * (nargs)
                self.addRule(rule, nop_func)
                rule = "unmapexpr ::=  %s %s" % (map_unpack_n, opname)
                self.addRule(rule, nop_func)
                call_token = tokens[i+1]
                rule = 'call ::= expr unmapexpr ' + call_token.kind
                self.addRule(rule, nop_func)
            elif opname == 'BEFORE_ASYNC_WITH':
                # Some Python 3.5+ async additions
                rules_str = """
                   async_with_stmt ::= expr
                   stmt ::= async_with_stmt

                   async_with_stmt ::= expr
                            BEFORE_ASYNC_WITH GET_AWAITABLE LOAD_CONST YIELD_FROM
                            SETUP_ASYNC_WITH POP_TOP suite_stmts_opt
                            POP_BLOCK LOAD_CONST
                            WITH_CLEANUP_START
                            GET_AWAITABLE LOAD_CONST YIELD_FROM
                            WITH_CLEANUP_FINISH END_FINALLY

                   stmt ::= async_with_as_stmt

                   async_with_as_stmt ::= expr
                               BEFORE_ASYNC_WITH GET_AWAITABLE LOAD_CONST YIELD_FROM
                               SETUP_ASYNC_WITH store suite_stmts_opt
                               POP_BLOCK LOAD_CONST
                               WITH_CLEANUP_START
                               GET_AWAITABLE LOAD_CONST YIELD_FROM
                               WITH_CLEANUP_FINISH END_FINALLY
                """
                self.addRule(rules_str, nop_func)
            elif opname == 'BUILD_MAP_UNPACK':
                self.addRule("""
                   expr       ::= unmap_dict
                   unmap_dict ::= dict_comp BUILD_MAP_UNPACK
                   """, nop_func)

            elif opname == 'SETUP_WITH':
                # Python 3.5+ has WITH_CLEANUP_START/FINISH
                rules_str = """
                  withstmt   ::= expr
                       SETUP_WITH POP_TOP suite_stmts_opt
                       POP_BLOCK LOAD_CONST COME_FROM_WITH
                       WITH_CLEANUP_START WITH_CLEANUP_FINISH END_FINALLY

                  withasstmt ::= expr
                       SETUP_WITH store suite_stmts_opt
                       POP_BLOCK LOAD_CONST COME_FROM_WITH
                       WITH_CLEANUP_START WITH_CLEANUP_FINISH END_FINALLY
                """
                self.addRule(rules_str, nop_func)
            pass
        return

    def custom_classfunc_rule(self, opname, token, customize,
                              seen_LOAD_BUILD_CLASS,
                              seen_GET_AWAITABLE_YIELD_FROM,
                              *args):
        args_pos, args_kw = self.get_pos_kw(token)

        # Additional exprs for * and ** args:
        #  0 if neither
        #  1 for CALL_FUNCTION_VAR or CALL_FUNCTION_KW
        #  2 for * and ** args (CALL_FUNCTION_VAR_KW).
        # Yes, this computation based on instruction name is a little bit hoaky.
        nak = ( len(opname)-len('CALL_FUNCTION') ) // 3
        uniq_param = args_kw + args_pos

        if seen_GET_AWAITABLE_YIELD_FROM:
            rule = ('async_call ::= expr ' +
                    ('pos_arg ' * args_pos) +
                    ('kwarg ' * args_kw) +
                    'expr ' * nak + token.kind +
                    ' GET_AWAITABLE LOAD_CONST YIELD_FROM')
            self.add_unique_rule(rule, token.kind, uniq_param, customize)
            self.add_unique_rule('expr ::= async_call', token.kind, uniq_param, customize)

        uniq_param = args_kw + args_pos
        if opname.startswith('CALL_FUNCTION_VAR'):
            # Python 3.5 changes the stack position of *args. KW args come
            # after *args.

            # Note: Python 3.6+ replaces CALL_FUNCTION_VAR and
            # CALL_FUNCTION_VAR_KW with CALL_FUNCTION_EX

            token.kind = self.call_fn_name(token)
            if opname.endswith('KW'):
                kw = 'expr '
            else:
                kw = ''
            rule = ('call ::= expr expr ' +
                    ('pos_arg ' * args_pos) +
                    ('kwarg ' * args_kw) + kw + token.kind)
            self.add_unique_rule(rule, token.kind, uniq_param, customize)
        else:
            super(Python35Parser, self).custom_classfunc_rule(opname, token, customize,
                                                              seen_LOAD_BUILD_CLASS,
                                                              seen_GET_AWAITABLE_YIELD_FROM,
                                                              *args)

class Python35ParserSingle(Python35Parser, PythonParserSingle):
    pass

if __name__ == '__main__':
    # Check grammar
    p = Python35Parser()
    p.check_grammar()
    from uncompyle6 import PYTHON_VERSION, IS_PYPY
    if PYTHON_VERSION == 3.5:
        lhs, rhs, tokens, right_recursive = p.check_sets()
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
