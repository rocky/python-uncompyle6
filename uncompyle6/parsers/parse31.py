#  Copyright (c) 2016-2017, 2022 Rocky Bernstein
"""
spark grammar differences over Python 3.2 for Python 3.1.
"""

from uncompyle6.parser import PythonParserSingle
from uncompyle6.parsers.parse32 import Python32Parser


class Python31Parser(Python32Parser):
    def p_31(self, args):
        """
        subscript2     ::= expr expr DUP_TOPX BINARY_SUBSCR

        setupwith      ::= DUP_TOP LOAD_ATTR store LOAD_ATTR CALL_FUNCTION_0 POP_TOP
        setupwithas    ::= DUP_TOP LOAD_ATTR store LOAD_ATTR CALL_FUNCTION_0 store
        with           ::= expr setupwith SETUP_FINALLY
                           suite_stmts_opt
                           POP_BLOCK LOAD_CONST COME_FROM_FINALLY
                           load delete WITH_CLEANUP END_FINALLY

        # Keeps Python 3.1 "with .. as" designator in the same position as it is in other version.
        setupwithas31  ::= setupwithas SETUP_FINALLY load delete

        withasstmt     ::= expr setupwithas31 store
                           suite_stmts_opt
                           POP_BLOCK LOAD_CONST COME_FROM_FINALLY
                           load delete WITH_CLEANUP END_FINALLY

        store ::= STORE_NAME
        load  ::= LOAD_FAST
        load  ::= LOAD_NAME
        """

    def remove_rules_31(self):
        self.remove_rules(
            """
        # DUP_TOP_TWO is DUP_TOPX in 3.1 and earlier
        subscript2 ::= expr expr DUP_TOP_TWO BINARY_SUBSCR

        # The were found using grammar coverage
        list_if     ::= expr jmp_false list_iter COME_FROM
        list_if_not ::= expr jmp_true list_iter COME_FROM
        """
        )

    def customize_grammar_rules(self, tokens, customize):
        super(Python31Parser, self).customize_grammar_rules(tokens, customize)
        self.remove_rules_31()
        return

    pass


class Python31ParserSingle(Python31Parser, PythonParserSingle):
    pass


if __name__ == "__main__":
    # Check grammar
    p = Python31Parser()
    p.remove_rules_31()
    p.check_grammar()
    from xdis.version_info import IS_PYPY, PYTHON_VERSION_TRIPLE

    if PYTHON_VERSION_TRIPLE[:2] == (3, 1):
        lhs, rhs, tokens, right_recursive, dup_rhs = p.check_sets()
        from uncompyle6.scanner import get_scanner

        s = get_scanner(PYTHON_VERSION_TRIPLE, IS_PYPY)
        opcode_set = set(s.opc.opname).union(
            set(
                """JUMP_BACK CONTINUE RETURN_END_IF COME_FROM
               LOAD_GENEXPR LOAD_ASSERT LOAD_SETCOMP LOAD_DICTCOMP LOAD_CLASSNAME
               LAMBDA_MARKER RETURN_LAST
            """.split()
            )
        )
        # FIXME: try this
        remain_tokens = set(tokens) - opcode_set
        import re

        remain_tokens = set([re.sub(r"_\d+$", "", t) for t in remain_tokens])
        remain_tokens = set([re.sub("_CONT$", "", t) for t in remain_tokens])
        remain_tokens = set(remain_tokens) - opcode_set
        print(remain_tokens)
        import sys

        if len(sys.argv) > 1:
            from spark_parser.spark import rule2str

            for rule in sorted(p.rule2name.items()):
                print(rule2str(rule[0]))
