#  Copyright (c) 2016-2017 Rocky Bernstein
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
        # withas is allowed as a "from future" in 2.5
        # 2.6 and 2.7 do something slightly different
        setupwithas ::= DUP_TOP LOAD_ATTR store LOAD_ATTR CALL_FUNCTION_0
                        setup_finally
        # opcode SETUP_WITH
        setupwith ::= DUP_TOP LOAD_ATTR STORE_NAME LOAD_ATTR CALL_FUNCTION_0 POP_TOP
        withstmt ::= expr setupwith SETUP_FINALLY suite_stmts_opt
                     POP_BLOCK LOAD_CONST COME_FROM with_cleanup

        store ::= STORE_FAST
        store ::= STORE_NAME

        tryelsestmt    ::= SETUP_EXCEPT suite_stmts_opt POP_BLOCK
                           try_middle else_suite COME_FROM

        # Python 2.6 omits the LOAD_FAST DELETE_FAST below
        # withas is allowed as a "from future" in 2.5
        withasstmt ::= expr setupwithas designator suite_stmts_opt
                       POP_BLOCK LOAD_CONST COME_FROM
                       with_cleanup

        with_cleanup ::= LOAD_FAST DELETE_FAST WITH_CLEANUP END_FINALLY
        with_cleanup ::= LOAD_NAME DELETE_NAME WITH_CLEANUP END_FINALLY


        kvlist ::= kvlist kv
        kv     ::= DUP_TOP expr ROT_TWO expr STORE_SUBSCR
        """

    def add_custom_rules(self, tokens, customize):
        # grammar rules inherited from Python 2.6
        self.remove_rules("""
        setupwith  ::= DUP_TOP LOAD_ATTR ROT_TWO LOAD_ATTR CALL_FUNCTION_0 POP_TOP
        withstmt   ::= expr setupwith SETUP_FINALLY suite_stmts_opt
                       POP_BLOCK LOAD_CONST COME_FROM WITH_CLEANUP END_FINALLY
        withasstmt ::= expr setupwithas designator suite_stmts_opt
                       POP_BLOCK LOAD_CONST COME_FROM WITH_CLEANUP END_FINALLY
        assert2    ::= assert_expr jmp_true LOAD_ASSERT expr CALL_FUNCTION_1 RAISE_VARARGS_1
        """)
        super(Python25Parser, self).add_custom_rules(tokens, customize)
        if self.version == 2.5:
            self.check_reduce['tryelsestmt'] = 'tokens'

    def reduce_is_invalid(self, rule, ast, tokens, first, last):
        invalid = super(Python25Parser,
                        self).reduce_is_invalid(rule, ast,
                                                tokens, first, last)
        if invalid:
            return invalid
        return False


class Python25ParserSingle(Python26Parser, PythonParserSingle):
    pass

if __name__ == '__main__':
    # Check grammar
    p = Python25Parser()
    p.check_grammar()
