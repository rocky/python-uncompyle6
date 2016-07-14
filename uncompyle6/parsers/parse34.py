#  Copyright (c) 2016 Rocky Bernstein
"""
spark grammar differences over Python3 for Python 3.4.2.
"""

from uncompyle6.parser import PythonParserSingle
from spark_parser import DEFAULT_DEBUG as PARSER_DEFAULT_DEBUG
from uncompyle6.parsers.parse3 import Python3Parser

class Python34Parser(Python3Parser):

    def __init__(self, debug_parser=PARSER_DEFAULT_DEBUG):
        super(Python34Parser, self).__init__(debug_parser)
        self.customized = {}

    def p_misc34(self, args):
        """
        # Python 3.5+ optimizes the trailing two JUMPS away

        for_block ::= l_stmts

        iflaststmtl ::= testexpr c_stmts_opt

        _ifstmts_jump ::= c_stmts_opt JUMP_FORWARD _come_from

        # We do the grammar hackery below for semantics
        # actions that want c_stmts_opt at index 1
        iflaststmt    ::= testexpr c_stmts_opt34
        c_stmts_opt34 ::= JUMP_BACK JUMP_ABSOLUTE c_stmts_opt

        # Python 3.3 added "yield from." Do it the same way as in
        # 3.3

        expr ::= yield_from
        yield_from ::= expr expr YIELD_FROM

        # Is this 3.4 only?
        yield_from ::= expr GET_ITER LOAD_CONST YIELD_FROM

        # Python 3.4+ has more loop optimization that removes
        # JUMP_FORWARD in some cases, and hence we also don't
        # see COME_FROM
        _ifstmts_jump ::= c_stmts_opt
        """
class Python34ParserSingle(Python34Parser, PythonParserSingle):
    pass


def info(args):
    # Check grammar
    # Should also add a way to dump grammar
    p = Python34Parser()
    p.checkGrammar()


if __name__ == '__main__':
    import sys
    info(sys.argv)
