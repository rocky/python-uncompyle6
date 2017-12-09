#  Copyright (c) 2016-2017 Rocky Bernstein
"""
spark grammar differences over Python 3.5 for Python 3.6.
"""

from uncompyle6.parser import PythonParserSingle
from spark_parser import DEFAULT_DEBUG as PARSER_DEFAULT_DEBUG
from uncompyle6.parsers.parse35 import Python35Parser

class Python36Parser(Python35Parser):

    def __init__(self, debug_parser=PARSER_DEFAULT_DEBUG):
        super(Python36Parser, self).__init__(debug_parser)
        self.customized = {}


    def p_36misc(self, args):
        """
        # 3.6 redoes how return_closure works
        return_closure   ::= LOAD_CLOSURE DUP_TOP STORE_NAME RETURN_VALUE RETURN_LAST

        stmt               ::= conditional_lambda
        conditional_lambda ::= expr jmp_false expr return_if_lambda
                               return_stmt_lambda LAMBDA_MARKER
        return_stmt_lambda ::= ret_expr RETURN_VALUE_LAMBDA
        return_if_lambda   ::= RETURN_END_IF_LAMBDA


        func_args36   ::= expr BUILD_TUPLE_0
        call          ::= func_args36 unmapexpr CALL_FUNCTION_EX
        call          ::= func_args36 build_map_unpack_with_call CALL_FUNCTION_EX_KW_1

        withstmt      ::= expr SETUP_WITH POP_TOP suite_stmts_opt POP_BLOCK LOAD_CONST
                          WITH_CLEANUP_START WITH_CLEANUP_FINISH END_FINALLY

        call          ::= expr expr CALL_FUNCTION_EX
        call          ::= expr expr expr CALL_FUNCTION_EX_KW_1

        for_block       ::= l_stmts_opt come_from_loops JUMP_BACK
        come_from_loops ::= COME_FROM_LOOP*


        # This might be valid in < 3.6
        and  ::= expr jmp_false expr

        # Adds a COME_FROM_ASYNC_WITH over 3.5
        # FIXME: remove corresponding rule for 3.5?
        async_with_as_stmt ::= expr
                               BEFORE_ASYNC_WITH GET_AWAITABLE LOAD_CONST YIELD_FROM
                               SETUP_ASYNC_WITH store
                               suite_stmts_opt
                               POP_BLOCK LOAD_CONST
                               COME_FROM_ASYNC_WITH
                               WITH_CLEANUP_START
                               GET_AWAITABLE LOAD_CONST YIELD_FROM
                               WITH_CLEANUP_FINISH END_FINALLY
        async_with_stmt ::= expr
                            BEFORE_ASYNC_WITH GET_AWAITABLE LOAD_CONST YIELD_FROM
                            SETUP_ASYNC_WITH POP_TOP suite_stmts_opt
                            POP_BLOCK LOAD_CONST
                            COME_FROM_ASYNC_WITH
                            WITH_CLEANUP_START
                            GET_AWAITABLE LOAD_CONST YIELD_FROM
                            WITH_CLEANUP_FINISH END_FINALLY

        except_suite ::= c_stmts_opt COME_FROM POP_EXCEPT jump_except COME_FROM

        # In 3.6+, A sequence of statements ending in a RETURN can cause
        # JUMP_FORWARD END_FINALLY to be omitted from try middle

        except_return    ::= POP_TOP POP_TOP POP_TOP return_stmts
        except_handler   ::= JUMP_FORWARD COME_FROM_EXCEPT except_return

        # Try middle following a return_stmts
        except_handler36 ::= COME_FROM_EXCEPT except_stmts END_FINALLY

        stmt             ::= try_except36
        try_except36     ::= SETUP_EXCEPT return_stmts except_handler36 opt_come_from_except
        """

    def add_custom_rules(self, tokens, customize):
        super(Python36Parser, self).add_custom_rules(tokens, customize)
        for i, token in enumerate(tokens):
            opname = token.kind

            if opname == 'FORMAT_VALUE':
                rules_str = """
                    expr ::= fstring_single
                    fstring_single ::= expr FORMAT_VALUE
                """
                self.add_unique_doc_rules(rules_str, customize)
            elif opname == 'BUILD_STRING':
                v = token.attr
                joined_str_n = "formatted_value_%s" % v
                rules_str = """
                    expr            ::= fstring_expr
                    fstring_expr    ::= expr FORMAT_VALUE
                    str             ::= LOAD_CONST
                    formatted_value ::= fstring_expr
                    formatted_value ::= str

                    expr                 ::= fstring_multi
                    fstring_multi        ::= joined_str BUILD_STRING
                    joined_str           ::= formatted_value+
                    fstring_multi        ::= %s BUILD_STRING
                    %s                   ::= %sBUILD_STRING
                """ % (joined_str_n, joined_str_n, "formatted_value " * v)
                self.add_unique_doc_rules(rules_str, customize)

    def custom_classfunc_rule(self, opname, token, customize,
                              possible_class_decorator,
                              seen_GET_AWAITABLE_YIELD_FROM, next_token):
        if opname.startswith('CALL_FUNCTION_KW'):
            values = 'expr ' * token.attr
            rule = 'call ::= expr kwargs_only_36 {token.kind}'.format(**locals())
            self.add_unique_rule(rule, token.kind, token.attr, customize)
            rule = 'kwargs_only_36 ::= {values} LOAD_CONST'.format(**locals())
            self.add_unique_rule(rule, token.kind, token.attr, customize)
        else:
            super(Python36Parser, self).custom_classfunc_rule(opname, token,
                                                              customize,
                                                              possible_class_decorator,
                                                              seen_GET_AWAITABLE_YIELD_FROM,
                                                              next_token)


class Python36ParserSingle(Python36Parser, PythonParserSingle):
    pass

if __name__ == '__main__':
    # Check grammar
    p = Python36Parser()
    p.check_grammar()
    from uncompyle6 import PYTHON_VERSION, IS_PYPY
    if PYTHON_VERSION == 3.6:
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
