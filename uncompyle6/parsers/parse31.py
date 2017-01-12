#  Copyright (c) 2016 Rocky Bernstein
"""
spark grammar differences over Python 3.2 for Python 3.1.
"""

from uncompyle6.parser import PythonParserSingle
from uncompyle6.parsers.parse32 import Python32Parser

class Python31Parser(Python32Parser):

    def p_31(self, args):
        """
        binary_subscr2 ::= expr expr DUP_TOPX BINARY_SUBSCR

        setupwith      ::= DUP_TOP LOAD_ATTR store LOAD_ATTR CALL_FUNCTION_0 POP_TOP
        setupwithas    ::= DUP_TOP LOAD_ATTR store LOAD_ATTR CALL_FUNCTION_0 store
        withstmt       ::= expr setupwith SETUP_FINALLY
                           suite_stmts_opt
                           POP_BLOCK LOAD_CONST COME_FROM_FINALLY
                           load del_stmt WITH_CLEANUP END_FINALLY

        # Keeps Python 3.1 withas desigator in the same position as it is in other version
        setupwithas31  ::= setupwithas SETUP_FINALLY load del_stmt

        withasstmt     ::= expr setupwithas31 designator
                           suite_stmts_opt
                           POP_BLOCK LOAD_CONST COME_FROM_FINALLY
                           load del_stmt WITH_CLEANUP END_FINALLY

        store ::= STORE_FAST
        store ::= STORE_NAME
        load  ::= LOAD_FAST
        load  ::= LOAD_NAME
        """

    def add_custom_rules(self, tokens, customize):
        super(Python31Parser, self).add_custom_rules(tokens, customize)
        return
    pass

class Python31ParserSingle(Python31Parser, PythonParserSingle):
    pass
