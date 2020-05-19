#  Copyright (c) 2019-2020 Rocky Bernstein

from spark_parser import DEFAULT_DEBUG as PARSER_DEFAULT_DEBUG
from uncompyle6.parser import PythonParserSingle
from uncompyle6.parsers.parse12 import Python12Parser


class Python11Parser(Python12Parser):
    def __init__(self, debug_parser=PARSER_DEFAULT_DEBUG):
        super(Python11Parser, self).__init__(debug_parser)
        self.customized = {}


class Python11ParserSingle(Python11Parser, PythonParserSingle):
    pass


if __name__ == "__main__":
    # Check grammar
    p = Python12Parser()
    p.check_grammar()
    p.dump_grammar()

# local variables:
# tab-width: 4
