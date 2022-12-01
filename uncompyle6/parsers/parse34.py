#  Copyright (c) 2017-2018 Rocky Bernstein

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
spark grammar differences over Python 3.3 for Python 3.4
"""

from uncompyle6.parser import PythonParserSingle
from uncompyle6.parsers.parse33 import Python33Parser


class Python34Parser(Python33Parser):

    def p_misc34(self, args):
        """
        expr ::= LOAD_ASSERT


        # passtmt is needed for semantic actions to add "pass"
        suite_stmts_opt ::= pass

        whilestmt     ::= SETUP_LOOP testexpr returns come_froms POP_BLOCK COME_FROM_LOOP

        # Seems to be needed starting 3.4.4 or so
        while1stmt    ::= SETUP_LOOP l_stmts
                          COME_FROM JUMP_BACK POP_BLOCK COME_FROM_LOOP
        while1stmt    ::= SETUP_LOOP l_stmts
                          POP_BLOCK COME_FROM_LOOP

        # FIXME the below masks a bug in not detecting COME_FROM_LOOP
        # grammar rules with COME_FROM -> COME_FROM_LOOP already exist
        whileelsestmt     ::= SETUP_LOOP testexpr l_stmts_opt JUMP_BACK POP_BLOCK
                              else_suitel COME_FROM

        while1elsestmt    ::= SETUP_LOOP l_stmts JUMP_BACK _come_froms POP_BLOCK else_suitel
                              COME_FROM_LOOP

        # Python 3.4+ optimizes the trailing two JUMPS away

        # This is 3.4 only
        yield_from ::= expr GET_ITER LOAD_CONST YIELD_FROM

        _ifstmts_jump ::= c_stmts_opt JUMP_ABSOLUTE JUMP_FORWARD COME_FROM
        """

    def customize_grammar_rules(self, tokens, customize):
        self.remove_rules("""
        yield_from    ::= expr expr YIELD_FROM
        # 3.4.2 has this. 3.4.4 may now
        # while1stmt ::= SETUP_LOOP l_stmts COME_FROM JUMP_BACK COME_FROM_LOOP
        """)
        super(Python34Parser, self).customize_grammar_rules(tokens, customize)
        return

class Python34ParserSingle(Python34Parser, PythonParserSingle):
    pass


if __name__ == '__main__':
    # Check grammar
    p = Python34Parser()
    p.check_grammar()
    from xdis.version_info import IS_PYPY, PYTHON_VERSION_TRIPLE
    if PYTHON_VERSION_TRIPLE[:2] == (3, 4):
        lhs, rhs, tokens, right_recursive, dup_rhs = p.check_sets()
        from uncompyle6.scanner import get_scanner
        s = get_scanner(PYTHON_VERSION_TRIPLE, IS_PYPY)
        opcode_set = set(s.opc.opname).union(set(
            """JUMP_BACK CONTINUE RETURN_END_IF COME_FROM
               LOAD_GENEXPR LOAD_ASSERT LOAD_SETCOMP LOAD_DICTCOMP LOAD_CLASSNAME
               LAMBDA_MARKER RETURN_LAST
            """.split()))
        remain_tokens = set(tokens) - opcode_set
        import re
        remain_tokens = set([re.sub(r'_\d+$', '',  t) for t in remain_tokens])
        remain_tokens = set([re.sub('_CONT$', '', t) for t in remain_tokens])
        remain_tokens = set(remain_tokens) - opcode_set
        print(remain_tokens)
        # print(sorted(p.rule2name.items()))
