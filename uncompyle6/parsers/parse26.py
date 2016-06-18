#  Copyright (c) 2016 Rocky Bernstein
"""
spark grammar differences over Python2 for Python 2.6.
"""

from uncompyle6.parser import PythonParserSingle
from spark_parser import DEFAULT_DEBUG as PARSER_DEFAULT_DEBUG
from uncompyle6.parsers.parse2 import Python2Parser

class Python26Parser(Python2Parser):

    def __init__(self, debug_parser=PARSER_DEFAULT_DEBUG):
        super(Python26Parser, self).__init__(debug_parser)
        self.customized = {}


    def p_lis_iter(self, args):
        '''
        list_iter ::= list_if JUMP_BACK
        '''

class Python26ParserSingle(Python2Parser, PythonParserSingle):
    pass

if __name__ == '__main__':
    # Check grammar
    p = Python26Parser()
    p.checkGrammar()
