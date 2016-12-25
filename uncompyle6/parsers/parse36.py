#  Copyright (c) 2016 Rocky Bernstein
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
        fstring_multi ::= fstring_expr_or_strs BUILD_STRING
        fstring_expr_or_strs ::= fstring_expr_or_str+

        func_args36   ::= expr BUILD_TUPLE_0
        call_function ::= func_args36 unmapexpr CALL_FUNCTION_EX
        """

    def add_custom_rules(self, tokens, customize):
        super(Python36Parser, self).add_custom_rules(tokens, customize)
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
