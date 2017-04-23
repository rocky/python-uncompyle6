#  Copyright (c) 2016 Rocky Bernstein
"""
spark grammar differences over Python 3.3 for Python 3.4
"""

from uncompyle6.parser import PythonParserSingle
from spark_parser import DEFAULT_DEBUG as PARSER_DEFAULT_DEBUG
from uncompyle6.parsers.parse33 import Python33Parser

class Python34Parser(Python33Parser):

    def __init__(self, debug_parser=PARSER_DEFAULT_DEBUG):
        super(Python34Parser, self).__init__(debug_parser)
        self.customized = {}

    def p_misc34(self, args):
        """
        expr ::= LOAD_ASSERT

        # Python 3.4+ optimizes the trailing two JUMPS away

        # Is this 3.4 only?
        yield_from ::= expr GET_ITER LOAD_CONST YIELD_FROM
        """
class Python34ParserSingle(Python34Parser, PythonParserSingle):
    pass


if __name__ == '__main__':
    # Check grammar
    p = Python34Parser()
    p.checkGrammar()
    from uncompyle6 import PYTHON_VERSION, IS_PYPY
    if PYTHON_VERSION == 3.4:
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
        remain_tokens = set([re.sub('_\d+$', '',  t) for t in remain_tokens])
        remain_tokens = set([re.sub('_CONT$', '', t) for t in remain_tokens])
        remain_tokens = set(remain_tokens) - opcode_set
        print(remain_tokens)
        # print(sorted(p.rule2name.items()))
