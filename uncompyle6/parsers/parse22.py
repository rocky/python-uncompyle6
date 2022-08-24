#  Copyright (c) 2016-2017, 2020 Rocky Bernstein
#  Copyright (c) 2000-2002 by hartmut Goebel <hartmut@goebel.noris.de>

from spark_parser import DEFAULT_DEBUG as PARSER_DEFAULT_DEBUG
from uncompyle6.parser import PythonParserSingle
from uncompyle6.parsers.parse23 import Python23Parser

class Python22Parser(Python23Parser):

    def __init__(self, debug_parser=PARSER_DEFAULT_DEBUG):
        super(Python22Parser, self).__init__(debug_parser)
        self.customized = {}

    def p_misc22(self, args):
        '''
        for_iter  ::= LOAD_CONST FOR_LOOP
        list_iter ::= list_if JUMP_FORWARD
                      COME_FROM POP_TOP COME_FROM
        list_for  ::= expr for_iter store list_iter CONTINUE JUMP_FORWARD
                      COME_FROM POP_TOP COME_FROM

        # Some versions of Python 2.2 have been found to generate
        # PRINT_ITEM_CONT for PRINT_ITEM
        print_items_stmt ::= expr PRINT_ITEM_CONT print_items_opt
        '''

    def customize_grammar_rules(self, tokens, customize):
        super(Python22Parser, self).customize_grammar_rules(tokens, customize)
        self.remove_rules("""
        kvlist ::= kvlist kv2
        """)
        if self.version[:2] <= (2, 2):
            # TODO: We may add something different or customize something
            del self.reduce_check_table["ifstmt"]


class Python22ParserSingle(Python23Parser, PythonParserSingle):
    pass

if __name__ == '__main__':
    # Check grammar
    p = Python22Parser()
    p.check_grammar()
    p.dump_grammar()

# local variables:
# tab-width: 4
