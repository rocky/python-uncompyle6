#  Copyright (c) 2019 Rocky Bernstein

from spark_parser import DEFAULT_DEBUG as PARSER_DEFAULT_DEBUG
from uncompyle6.parser import PythonParserSingle
from uncompyle6.parsers.parse13 import Python13Parser


class Python12Parser(Python13Parser):
    def __init__(self, debug_parser=PARSER_DEFAULT_DEBUG):
        super(Python12Parser, self).__init__(debug_parser)
        self.customized = {}


class Python12ParserSingle(Python12Parser, PythonParserSingle):
    pass


if __name__ == "__main__":
    # Check grammar
    p = Python12Parser()
    p.check_grammar()
    p.dump_grammar()

# local variables:
# tab-width: 4
