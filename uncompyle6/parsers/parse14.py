#  Copyright (c) 2018 Rocky Bernstein

from spark_parser import DEFAULT_DEBUG as PARSER_DEFAULT_DEBUG
from uncompyle6.parser import PythonParserSingle
from uncompyle6.parsers.parse15 import Python15Parser

class Python14Parser(Python15Parser):

    def p_misc14(self, args):
        """
        # Not much here yet, but will probably need to add UNARY_CALL, BINARY_CALL,
        # RAISE_EXCEPTION, BUILD_FUNCTION, UNPACK_ARG, UNPACK_VARARG, LOAD_LOCAL,
        # SET_FUNC_ARGS, and RESERVE_FAST

        # Not strictly needed, but tidies up output
        stmt     ::= doc_junk
        doc_junk ::= LOAD_CONST POP_TOP

        # Not sure why later Python's omit the COME_FROM
        jb_pop14  ::= JUMP_BACK COME_FROM POP_TOP

        whileelsestmt ::= SETUP_LOOP testexpr l_stmts_opt
                          jb_pop14
                          POP_BLOCK else_suitel COME_FROM

        print_items_nl_stmt ::= expr PRINT_ITEM_CONT print_items_opt PRINT_NEWLINE_CONT


        # 1.4 doesn't have linenotab, and although this shouldn't
        # be a show stopper, our CONTINUE detection is off here.
        continue ::= JUMP_BACK
        """

    def __init__(self, debug_parser=PARSER_DEFAULT_DEBUG):
        super(Python14Parser, self).__init__(debug_parser)
        self.customized = {}

    def customize_grammar_rules(self, tokens, customize):
        super(Python14Parser, self).customize_grammar_rules(tokens, customize)
        self.remove_rules("""
        whileelsestmt ::= SETUP_LOOP testexpr l_stmts_opt
                          jb_pop
                          POP_BLOCK else_suitel COME_FROM
        """)
        self.check_reduce['doc_junk'] = 'tokens'


    def reduce_is_invalid(self, rule, ast, tokens, first, last):
        invalid = super(Python14Parser,
                        self).reduce_is_invalid(rule, ast,
                                                tokens, first, last)
        if invalid or tokens is None:
            return invalid
        if rule[0] == 'doc_junk':
            return not isinstance(tokens[first].pattr, str)



class Python14ParserSingle(Python14Parser, PythonParserSingle):
    pass

if __name__ == '__main__':
    # Check grammar
    p = Python14Parser()
    p.check_grammar()
    p.dump_grammar()

# local variables:
# tab-width: 4
