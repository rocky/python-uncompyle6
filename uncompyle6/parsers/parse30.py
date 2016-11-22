#  Copyright (c) 2016 Rocky Bernstein
"""
spark grammar differences over Python 3.1 for Python 3.0.
"""

from uncompyle6.parser import PythonParserSingle
from uncompyle6.parsers.parse3 import Python3Parser

class Python30Parser(Python3Parser):

    def p_30(self, args):
        """
        # Store locals is only in Python 3.0 to 3.3
        stmt         ::= store_locals
        store_locals ::= LOAD_FAST STORE_LOCALS


        # In many ways Python 3.0 code generation is more like Python 2.6 than
        # it is 2.7 or 3.1. So we have a number of 2.6ish (and before) rules below

        _ifstmts_jump  ::= c_stmts_opt JUMP_FORWARD come_froms POP_TOP COME_FROM
        jmp_true       ::= JUMP_IF_TRUE POP_TOP
        jmp_false      ::= JUMP_IF_FALSE POP_TOP

        # Used to keep index order the same in semantic actions
        jb_pop_top     ::= JUMP_BACK POP_TOP

        while1stmt ::= SETUP_LOOP l_stmts COME_FROM_LOOP

        else_suitel ::= l_stmts COME_FROM_LOOP JUMP_BACK

        ifelsestmtl ::= testexpr c_stmts_opt jb_pop_top else_suitel

        withasstmt    ::= expr setupwithas designator suite_stmts_opt
                          POP_BLOCK LOAD_CONST COME_FROM_FINALLY
                          LOAD_FAST DELETE_FAST WITH_CLEANUP END_FINALLY
        setupwithas   ::= DUP_TOP LOAD_ATTR STORE_FAST LOAD_ATTR CALL_FUNCTION_0 setup_finally
        setup_finally ::= STORE_FAST SETUP_FINALLY LOAD_FAST DELETE_FAST
        """

class Python30ParserSingle(Python30Parser, PythonParserSingle):
    pass
