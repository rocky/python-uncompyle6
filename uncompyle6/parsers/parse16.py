#  Copyright (c) 2019 Rocky Bernstein

from spark_parser import DEFAULT_DEBUG as PARSER_DEFAULT_DEBUG
from uncompyle6.parser import PythonParserSingle, nop_func
from uncompyle6.parsers.parse21 import Python21Parser

class Python16Parser(Python21Parser):

    def __init__(self, debug_parser=PARSER_DEFAULT_DEBUG):
        super(Python16Parser, self).__init__(debug_parser)
        self.customized = {}

    def p_import16(self, args):
        """
        import      ::= filler IMPORT_NAME STORE_FAST
        import      ::= filler IMPORT_NAME STORE_NAME

        import_from ::= filler IMPORT_NAME importlist
        import_from ::= filler filler IMPORT_NAME importlist POP_TOP

        importlist  ::= importlist IMPORT_FROM
        importlist  ::= IMPORT_FROM
        """

    def customize_grammar_rules(self, tokens, customize):
        super(Python16Parser, self).customize_grammar_rules(tokens, customize)
        for i, token in enumerate(tokens):
            opname = token.kind
            opname_base = opname[:opname.rfind('_')]

            if opname_base == 'UNPACK_LIST':
                self.addRule("store ::= unpack_list", nop_func)



class Python16ParserSingle(Python16Parser, PythonParserSingle):
    pass

if __name__ == '__main__':
    # Check grammar
    p = Python15Parser()
    p.check_grammar()
    p.dump_grammar()

# local variables:
# tab-width: 4
