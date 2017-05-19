#  Copyright (c) 2016 Rocky Bernstein
"""
spark grammar differences over Python 3.5 for Python 3.6.
"""
from __future__ import print_function

from uncompyle6.parser import PythonParserSingle
from spark_parser import DEFAULT_DEBUG as PARSER_DEFAULT_DEBUG
from uncompyle6.parsers.parse35 import Python35Parser

class Python36Parser(Python35Parser):

    def __init__(self, debug_parser=PARSER_DEFAULT_DEBUG):
        super(Python36Parser, self).__init__(debug_parser)
        self.customized = {}

    def p_loop_stmt3(self, args):
        """
        # The range of values in arguments in 3.6 has been reduced from 2**16 to 2**8.
        # As a result,  EXTENDED_ARG needs to be used where it didn't before.
        # Is this relevant to < 3.6 as well?


        setup_loop        ::= SETUP_LOOP
        setup_loop        ::= EXTENDED_ARG SETUP_LOOP

        forstmt           ::= setup_loop expr _for designator for_block POP_BLOCK
                              opt_come_from_loop

        forelsestmt       ::= setup_loop expr _for designator for_block POP_BLOCK else_suite
                              COME_FROM_LOOP

        forelselaststmt   ::= setup_loop expr _for designator for_block POP_BLOCK else_suitec
                              COME_FROM_LOOP

        forelselaststmtl  ::= setup_loop expr _for designator for_block POP_BLOCK else_suitel
                              COME_FROM_LOOP

        whilestmt         ::= setup_loop testexpr l_stmts_opt COME_FROM jump_back POP_BLOCK
                              COME_FROM_LOOP

        whilestmt         ::= setup_loop testexpr l_stmts_opt jump_back POP_BLOCK
                              COME_FROM_LOOP

        whileTruestmt     ::= setup_loop l_stmts_opt JUMP_BACK POP_BLOCK COME_FROM_LOOP
        """


    def p_36misc(self, args):
        """
        # The range of values in arguments in 3.6 has been reduced from 2**16 to 2**8.
        # As a result,  EXTENDED_ARG needs to be used where it didn't before.
        # Is this relevant to < 3.6 as well?

        jmp_false ::= EXTENDED_ARG POP_JUMP_IF_FALSE
        jmp_true  ::= EXTENDED_ARG POP_JUMP_IF_TRUE
        _jump     ::= EXTENDED_ARG JUMP_BACK
        jump_back ::= EXTENDED_ARG JUMP_BACK

        continue_stmt ::= EXTENDED_ARG CONTINUE
        continue_stmt ::= EXTENDED_ARG CONTINUE_LOOP

        for_block ::= l_stmts_opt opt_come_from_loop jump_back
        cmp_list1 ::= expr DUP_TOP ROT_THREE COMPARE_OP
                      EXTENDED_ARG JUMP_IF_FALSE_OR_POP cmp_list2 COME_FROM


        # 3.6 redoes how return_closure works
        return_closure ::= LOAD_CLOSURE DUP_TOP STORE_NAME RETURN_VALUE RETURN_LAST

        expr ::= LOAD_NAME EXTENDED_ARG
        expr ::= LOAD_CONST EXTENDED_ARG

        fstring_multi ::= fstring_expr_or_strs BUILD_STRING
        fstring_expr_or_strs ::= fstring_expr_or_str+

        func_args36   ::= expr BUILD_TUPLE_0
        call_function ::= func_args36 unmapexpr CALL_FUNCTION_EX

        withstmt ::= expr SETUP_WITH POP_TOP suite_stmts_opt POP_BLOCK LOAD_CONST
                     WITH_CLEANUP_START WITH_CLEANUP_FINISH END_FINALLY

        call_function ::= expr expr CALL_FUNCTION_EX
        call_function ::= expr expr expr CALL_FUNCTION_EX_KW
        """

    def add_custom_rules(self, tokens, customize):
        super(Python36Parser, self).add_custom_rules(tokens, customize)
        self.remove_rule("""
        forstmt           ::= SETUP_LOOP expr _for designator for_block POP_BLOCK
                              opt_come_from_loop

        forelsestmt       ::= SETUP_LOOP expr _for designator for_block POP_BLOCK else_suite
                              COME_FROM_LOOP

        forelselaststmt   ::= SETUP_LOOP expr _for designator for_block POP_BLOCK else_suitec
                              COME_FROM_LOOP

        forelselaststmtl  ::= SETUP_LOOP expr _for designator for_block POP_BLOCK else_suitel
                              COME_FROM_LOOP

        whilestmt         ::= SETUP_LOOP testexpr l_stmts_opt COME_FROM jump_back POP_BLOCK
                              COME_FROM_LOOP

        whilestmt         ::= SETUP_LOOP testexpr l_stmts_opt jump_back POP_BLOCK
                              COME_FROM_LOOP

        whileTruestmt     ::= SETUP_LOOP l_stmts_opt JUMP_BACK POP_BLOCK COME_FROM_LOOP
                              COME_FROM_LOOP
        """)

        for i, token in enumerate(tokens):
            opname = token.type

            if opname == 'FORMAT_VALUE':
                rules_str = """
                    expr ::= fstring_single
                    fstring_single ::= expr FORMAT_VALUE
                """
                self.add_unique_doc_rules(rules_str, customize)
            elif opname == 'BUILD_STRING':
                v = token.attr
                fstring_expr_or_str_n = "fstring_expr_or_str_%s" % v
                rules_str = """
                    expr ::= fstring_expr
                    fstring_expr ::= expr FORMAT_VALUE
                    str ::= LOAD_CONST
                    fstring_expr_or_str ::= fstring_expr
                    fstring_expr_or_str ::= str

                    expr ::= fstring_multi
                    fstring_multi ::= %s BUILD_STRING
                    %s ::= %sBUILD_STRING
                """ % (fstring_expr_or_str_n, fstring_expr_or_str_n, "fstring_expr_or_str " * v)
                self.add_unique_doc_rules(rules_str, customize)

    def custom_classfunc_rule(self, opname, token, customize):

        if opname.startswith('CALL_FUNCTION_KW'):
            values = 'expr ' * token.attr
            rule = 'call_function ::= expr kwargs_only_36 {token.type}'.format(**locals())
            self.add_unique_rule(rule, token.type, token.attr, customize)
            rule = 'kwargs_only_36 ::= {values} LOAD_CONST'.format(**locals())
            self.add_unique_rule(rule, token.type, token.attr, customize)
        else:
            super(Python36Parser, self).custom_classfunc_rule(opname, token, customize)


class Python36ParserSingle(Python36Parser, PythonParserSingle):
    pass

if __name__ == '__main__':
    # Check grammar
    p = Python36Parser()
    p.checkGrammar()
    from uncompyle6 import PYTHON_VERSION, IS_PYPY
    if PYTHON_VERSION == 3.6:
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
