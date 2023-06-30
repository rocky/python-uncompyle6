#  Copyright (c) 2018, 2023 Rocky Bernstein

from spark_parser import DEFAULT_DEBUG as PARSER_DEFAULT_DEBUG

from uncompyle6.parser import PythonParserSingle
from uncompyle6.parsers.parse14 import Python14Parser


class Python13Parser(Python14Parser):
    def p_misc13(self, args):
        """
        # Nothing here yet, but will need to add LOAD_GLOBALS
        """

    def __init__(self, debug_parser=PARSER_DEFAULT_DEBUG):
        super(Python13Parser, self).__init__(debug_parser)
        self.customized = {}

    # def customize_grammar_rules(self, tokens, customize):
    #     super(Python13Parser, self).customize_grammar_rules(tokens, customize)
    #     self.remove_rules("""
    #     whileelsestmt ::= SETUP_LOOP testexpr l_stmts_opt
    #                       jb_pop
    #                       POP_BLOCK else_suitel COME_FROM
    #     """)
    #     self.check_reduce['doc_junk'] = 'tokens'

    # def reduce_is_invalid(self, rule, ast, tokens, first, last):
    #     invalid = super(Python14Parser,
    #                     self).reduce_is_invalid(rule, ast,
    #                                             tokens, first, last)
    #     if invalid or tokens is None:
    #         return invalid
    #     if rule[0] == 'doc_junk':
    #         return not isinstance(tokens[first].pattr, str)


class Python13ParserSingle(Python13Parser, PythonParserSingle):
    pass


if __name__ == "__main__":
    # Check grammar
    p = Python13Parser()
    p.check_grammar()
    p.dump_grammar()

# local variables:
# tab-width: 4
