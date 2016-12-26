#  Copyright (c) 2016 Rocky Bernstein
"""
spark grammar differences over Python2.6 for Python 2.5.
"""

from uncompyle6.parser import PythonParserSingle
from spark_parser import DEFAULT_DEBUG as PARSER_DEFAULT_DEBUG
from uncompyle6.parsers.parse26 import Python26Parser

class Python25Parser(Python26Parser):
    def __init__(self, debug_parser=PARSER_DEFAULT_DEBUG):
        super(Python25Parser, self).__init__(debug_parser)
        self.customized = {}

    def p_misc25(self, args):
        """
        # If "return_if_stmt" is in a loop, a JUMP_BACK can be emitted. In 2.6 the
        # JUMP_BACK doesn't appear

        return_if_stmt ::= ret_expr  RETURN_END_IF JUMP_BACK

        # Python 2.6 uses ROT_TWO instead of the STORE_xxx
        setupwithas ::= DUP_TOP LOAD_ATTR store LOAD_ATTR CALL_FUNCTION_0
                        setup_finally

        store ::= STORE_FAST
        store ::= STORE_NAME

        # Python 2.6 omits ths LOAD_FAST DELETE_FAST below
        withasstmt ::= expr setupwithas designator suite_stmts_opt
                       POP_BLOCK LOAD_CONST COME_FROM
                       with_cleanup

        with_cleanup ::= LOAD_FAST DELETE_FAST WITH_CLEANUP END_FINALLY
        with_cleanup ::= LOAD_NAME DELETE_NAME WITH_CLEANUP END_FINALLY
        """

    def add_custom_rules(self, tokens, customize):
        super(Python25Parser, self).add_custom_rules(tokens, customize)
        if self.version == 2.5:
            self.check_reduce['tryelsestmt'] = 'tokens'

    def reduce_is_invalid(self, rule, ast, tokens, first, last):
        invalid = super(Python25Parser,
                        self).reduce_is_invalid(rule, ast,
                                                tokens, first, last)
        if invalid:
            return invalid
        lhs = rule[0]
        if lhs in ('tryelsestmt', ):
            # The end of the else part of try/else come_from has to come
            # from an END_FINALLY statement
            if tokens[last-1].type.startswith('COME_FROM'):
                end_finally_offset = int(tokens[last-1].pattr)
                current  = first
                while current < last:
                    offset = tokens[current].offset
                    if offset == end_finally_offset:
                        return tokens[current].type != 'END_FINALLY'
                    current += 1
        return False


class Python25ParserSingle(Python26Parser, PythonParserSingle):
    pass

if __name__ == '__main__':
    # Check grammar
    p = Python25Parser()
    p.checkGrammar()
