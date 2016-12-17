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
        # Python 3.5+ has WITH_CLEANUP_START/FINISH

        withstmt ::= expr SETUP_WITH exprlist suite_stmts_opt
                    POP_BLOCK LOAD_CONST COME_FROM_WITH
                    WITH_CLEANUP_START WITH_CLEANUP_FINISH END_FINALLY

        withstmt ::= expr SETUP_WITH POP_TOP suite_stmts_opt
                     POP_BLOCK LOAD_CONST COME_FROM_WITH
                     WITH_CLEANUP_START WITH_CLEANUP_FINISH END_FINALLY

        withasstmt ::= expr SETUP_WITH designator suite_stmts_opt
                POP_BLOCK LOAD_CONST COME_FROM_WITH
                WITH_CLEANUP_START WITH_CLEANUP_FINISH END_FINALLY

        inplace_op ::= INPLACE_MATRIX_MULTIPLY
        binary_op  ::= BINARY_MATRIX_MULTIPLY

        # Python 3.5+ does jump optimization
        # In <.3.5 the below is a JUMP_FORWARD to a JUMP_ABSOLUTE.
        # in return_stmt, we will need the semantic actions in pysource.py
        # to work out whether to dedent or not based on the presence of
        # RETURN_END_IF vs RETURN_VALUE

        ifelsestmtc ::= testexpr c_stmts_opt JUMP_FORWARD else_suitec
        # ifstmt ::= testexpr c_stmts_opt

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
