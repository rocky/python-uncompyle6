#  Copyright (c) 2017 Rocky Bernstein
"""
spark grammar differences over Python 3.6 for Python 3.7
"""
from __future__ import print_function

from uncompyle6.parser import PythonParserSingle
from spark_parser import DEFAULT_DEBUG as PARSER_DEFAULT_DEBUG
from uncompyle6.parsers.parse36 import Python37Parser

class Python36Parser(Python35Parser):

    def __init__(self, debug_parser=PARSER_DEFAULT_DEBUG):
        super(Python37Parser, self).__init__(debug_parser)
        self.customized = {}


class Python37ParserSingle(Python37Parser, PythonParserSingle):
    pass

if __name__ == '__main__':
    # Check grammar
    p = Python37Parser()
    p.check_grammar()
    from uncompyle6 import PYTHON_VERSION, IS_PYPY
    if PYTHON_VERSION == 3.7:
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
