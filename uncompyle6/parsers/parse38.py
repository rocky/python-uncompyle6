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
spark grammar differences over Python 3.7 for Python 3.8
"""
from __future__ import print_function

from uncompyle6.parser import PythonParserSingle
from spark_parser import DEFAULT_DEBUG as PARSER_DEFAULT_DEBUG
from uncompyle6.parsers.parse37 import Python37Parser

class Python38Parser(Python37Parser):

    def p_38misc(self, args):
        """
        stmt               ::= for38
        stmt               ::= forelsestmt38
        stmt               ::= forelselaststmt38
        stmt               ::= forelselaststmtl38
        stmt               ::= tryfinally38
        stmt               ::= try_except_ret38

        # FIXME this should be restricted to being inside a try block
        stmt               ::= except_ret38

        for38              ::= expr get_iter store for_block JUMP_BACK
        for38              ::= expr for_iter store for_block JUMP_BACK
        for38              ::= expr for_iter store for_block JUMP_BACK POP_BLOCK

        forelsestmt38      ::= expr for_iter store for_block POP_BLOCK else_suite
        forelselaststmt38  ::= expr for_iter store for_block POP_BLOCK else_suitec
        forelselaststmtl38 ::= expr for_iter store for_block POP_BLOCK else_suitel
        whilestmt          ::= testexpr l_stmts_opt COME_FROM JUMP_BACK POP_BLOCK
        whilestmt          ::= testexpr l_stmts_opt JUMP_BACK POP_BLOCK
        whilestmt          ::= testexpr returns               POP_BLOCK
        while1elsestmt     ::=          l_stmts     JUMP_BACK
        whileelsestmt      ::= testexpr l_stmts     JUMP_BACK POP_BLOCK
        whileTruestmt      ::= l_stmts              JUMP_BACK POP_BLOCK
        while1stmt         ::= l_stmts COME_FROM_LOOP
        while1stmt         ::= l_stmts COME_FROM JUMP_BACK COME_FROM_LOOP
        while1elsestmt     ::= l_stmts JUMP_BACK
        whileTruestmt      ::= l_stmts JUMP_BACK NOP
        whileTruestmt      ::= l_stmts JUMP_BACK POP_BLOCK NOP
        for_block          ::= l_stmts_opt _come_from_loops JUMP_BACK

        except_cond1       ::= DUP_TOP expr COMPARE_OP jmp_false
                               POP_TOP POP_TOP POP_TOP
                               POP_EXCEPT
        try_except         ::= SETUP_FINALLY suite_stmts_opt POP_BLOCK
                               except_handler38
        try_except_ret38   ::= SETUP_FINALLY expr POP_BLOCK
                               RETURN_VALUE except_ret38a
        except_ret38       ::= SETUP_FINALLY expr ROT_FOUR POP_BLOCK POP_EXCEPT
                               CALL_FINALLY RETURN_VALUE COME_FROM_FINALLY
                               suite_stmts_opt END_FINALLY
        except_ret38a      ::= COME_FROM_FINALLY POP_TOP POP_TOP POP_TOP
                               expr ROT_FOUR
                               POP_EXCEPT RETURN_VALUE END_FINALLY
        except_handler38   ::= JUMP_FORWARD COME_FROM_FINALLY
                               except_stmts END_FINALLY opt_come_from_except
        tryfinallystmt     ::= SETUP_FINALLY suite_stmts_opt POP_BLOCK
                               BEGIN_FINALLY COME_FROM_FINALLY suite_stmts_opt
                               END_FINALLY
        tryfinally38       ::= SETUP_FINALLY POP_BLOCK CALL_FINALLY
                               returns
                               COME_FROM_FINALLY END_FINALLY suite_stmts
        tryfinally38       ::= SETUP_FINALLY POP_BLOCK CALL_FINALLY
                               returns
                               COME_FROM_FINALLY POP_FINALLY returns
                               END_FINALLY
        tryfinally_return_stmt ::= SETUP_FINALLY suite_stmts_opt POP_BLOCK
                                   BEGIN_FINALLY COME_FROM_FINALLY
                                   POP_FINALLY suite_stmts_opt END_FINALLY

        """

    def __init__(self, debug_parser=PARSER_DEFAULT_DEBUG):
        super(Python38Parser, self).__init__(debug_parser)
        self.customized = {}

    def customize_grammar_rules(self, tokens, customize):
        self.remove_rules("""
           stmt               ::= for
           stmt               ::= forelsestmt
           stmt               ::= try_except38

           for                ::= SETUP_LOOP expr for_iter store for_block POP_BLOCK
           for                ::= SETUP_LOOP expr for_iter store for_block POP_BLOCK NOP

           for_block          ::= l_stmts_opt COME_FROM_LOOP JUMP_BACK
           forelsestmt        ::= SETUP_LOOP expr for_iter store for_block POP_BLOCK else_suite
           forelselaststmt    ::= SETUP_LOOP expr for_iter store for_block POP_BLOCK else_suitec
           forelselaststmtl   ::= SETUP_LOOP expr for_iter store for_block POP_BLOCK else_suitel
           try_except         ::= SETUP_EXCEPT suite_stmts_opt POP_BLOCK
                                  except_handler opt_come_from_except
           tryfinallystmt     ::= SETUP_FINALLY suite_stmts_opt POP_BLOCK
                                  LOAD_CONST COME_FROM_FINALLY suite_stmts_opt
                                  END_FINALLY
           tryfinally36       ::= SETUP_FINALLY returns
                                  COME_FROM_FINALLY suite_stmts_opt END_FINALLY
           tryfinally_return_stmt ::= SETUP_FINALLY suite_stmts_opt POP_BLOCK
                                      LOAD_CONST COME_FROM_FINALLY


        """)
        super(Python37Parser, self).customize_grammar_rules(tokens, customize)

class Python38ParserSingle(Python38Parser, PythonParserSingle):
    pass

if __name__ == '__main__':
    # Check grammar
    p = Python38Parser()
    p.check_grammar()
    from uncompyle6 import PYTHON_VERSION, IS_PYPY
    if PYTHON_VERSION == 3.8:
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
