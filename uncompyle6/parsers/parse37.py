#  Copyright (c) 2017-2019 Rocky Bernstein
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
spark grammar differences over Python 3.6 for Python 3.7
"""

from uncompyle6.parser import PythonParserSingle
from spark_parser import DEFAULT_DEBUG as PARSER_DEFAULT_DEBUG
from uncompyle6.parsers.parse36 import Python36Parser

class Python37Parser(Python36Parser):

    def __init__(self, debug_parser=PARSER_DEFAULT_DEBUG):
        super(Python37Parser, self).__init__(debug_parser)
        self.customized = {}

    def p_37misc(self, args):
        """
        # Where does the POP_TOP really belong?
        stmt     ::= import37
        import37 ::= import POP_TOP

        async_for_stmt     ::= SETUP_LOOP expr
                               GET_AITER
                               SETUP_EXCEPT GET_ANEXT LOAD_CONST
                               YIELD_FROM
                               store
                               POP_BLOCK JUMP_FORWARD COME_FROM_EXCEPT DUP_TOP
                               LOAD_GLOBAL COMPARE_OP POP_JUMP_IF_TRUE
                               END_FINALLY COME_FROM
                               for_block
                               COME_FROM
                               POP_TOP POP_TOP POP_TOP POP_EXCEPT POP_TOP POP_BLOCK
                               COME_FROM_LOOP

        async_forelse_stmt ::= SETUP_LOOP expr
                               GET_AITER
                               SETUP_EXCEPT GET_ANEXT LOAD_CONST
                               YIELD_FROM
                               store
                               POP_BLOCK JUMP_FORWARD COME_FROM_EXCEPT DUP_TOP
                               LOAD_GLOBAL COMPARE_OP POP_JUMP_IF_TRUE
                               END_FINALLY COME_FROM
                               for_block
                               COME_FROM
                               POP_TOP POP_TOP POP_TOP POP_EXCEPT POP_TOP POP_BLOCK
                               else_suite COME_FROM_LOOP

        # Is there a pattern here?
        attributes ::= IMPORT_FROM ROT_TWO POP_TOP IMPORT_FROM

        attribute37   ::= expr LOAD_METHOD
        expr          ::= attribute37

        # FIXME: generalize and specialize
        call        ::= expr CALL_METHOD_0

        testtrue         ::= compare_chained37

        compare_chained37   ::= expr compare_chained1a_37
        compare_chained37   ::= expr compare_chained1b_37
        compare_chained2a_37 ::= expr COMPARE_OP POP_JUMP_IF_TRUE JUMP_FORWARD
        compare_chained2b_37 ::= expr COMPARE_OP COME_FROM POP_JUMP_IF_FALSE JUMP_FORWARD ELSE
        compare_chained1a_37 ::= expr DUP_TOP ROT_THREE COMPARE_OP POP_JUMP_IF_FALSE
                                 compare_chained2a_37  ELSE POP_TOP COME_FROM
        compare_chained1b_37 ::= expr DUP_TOP ROT_THREE COMPARE_OP POP_JUMP_IF_FALSE
                                 compare_chained2b_37 POP_TOP JUMP_FORWARD COME_FROM
        """

    def customize_grammar_rules(self, tokens, customize):
        self.remove_rules("""
          async_forelse_stmt ::= SETUP_LOOP expr
                                 GET_AITER
                                 LOAD_CONST YIELD_FROM SETUP_EXCEPT GET_ANEXT LOAD_CONST
                                 YIELD_FROM
                                 store
                                 POP_BLOCK JUMP_FORWARD COME_FROM_EXCEPT DUP_TOP
                                 LOAD_GLOBAL COMPARE_OP POP_JUMP_IF_FALSE
                                 POP_TOP POP_TOP POP_TOP POP_EXCEPT POP_BLOCK
                                 JUMP_ABSOLUTE END_FINALLY COME_FROM
                                 for_block POP_BLOCK
                                 else_suite COME_FROM_LOOP
        """)
        super(Python37Parser, self).customize_grammar_rules(tokens, customize)

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
        remain_tokens = set([re.sub(r'_\d+$', '', t) for t in remain_tokens])
        remain_tokens = set([re.sub('_CONT$', '', t) for t in remain_tokens])
        remain_tokens = set(remain_tokens) - opcode_set
        print(remain_tokens)
        # print(sorted(p.rule2name.items()))
