#  Copyright (c) 2019 Rocky Bernstein

from spark_parser import DEFAULT_DEBUG as PARSER_DEFAULT_DEBUG
from uncompyle6.parser import PythonParserSingle
from uncompyle6.parsers.parse11 import Python11Parser


class Python10Parser(Python11Parser):
    def __init__(self, debug_parser=PARSER_DEFAULT_DEBUG):
        super(Python10Parser, self).__init__(debug_parser)
        self.customized = {}


class Python10ParserSingle(Python10Parser, PythonParserSingle):
    pass


if __name__ == "__main__":
    # Check grammar
    p = Python10Parser()
    p.check_grammar()
    p.dump_grammar()

# local variables:
# tab-width: 4
