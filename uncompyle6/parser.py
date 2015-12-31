#  Copyright (c) 1999 John Aycock
#  Copyright (c) 2000-2002 by hartmut Goebel <h.goebel@crazy-compilers.com>
#  Copyright (c) 2005 by Dan Pascu <dan@windowmaker.org>
#  Copyright (c) 2015 Rocky Bernstein
"""
Common spark parser routines Python.
"""

from __future__ import print_function

import sys

from uncompyle6.code import iscode
from uncompyle6.parsers.spark import GenericASTBuilder, DEFAULT_DEBUG as PARSER_DEFAULT_DEBUG

class ParserError(Exception):
    def __init__(self, token, offset):
        self.token = token
        self.offset = offset

    def __str__(self):
        return "Syntax error at or near `%r' token at offset %s\n" % \
               (self.token, self.offset)

nop_func = lambda self, args: None

class PythonParser(GenericASTBuilder):

    def cleanup(self):
        """
        Remove recursive references to allow garbage
        collector to collect this object.
        """
        for dict in (self.rule2func, self.rules, self.rule2name):
            for i in list(dict.keys()):
                dict[i] = None
        for i in dir(self):
            setattr(self, i, None)

    def error(self, token):
            raise ParserError(token, token.offset)

    def typestring(self, token):
        return token.type

    def nonterminal(self, nt, args):
        collect = ('stmts', 'exprlist', 'kvlist', '_stmts', 'print_items')

        if nt in collect and len(args) > 1:
            #
            #  Collect iterated thingies together.
            #
            rv = args[0]
            rv.append(args[1])
        else:
            rv = GenericASTBuilder.nonterminal(self, nt, args)
        return rv

    def __ambiguity(self, children):
        # only for debugging! to be removed hG/2000-10-15
        print(children)
        return GenericASTBuilder.ambiguity(self, children)

    def resolve(self, list):
        if len(list) == 2 and 'funcdef' in list and 'assign' in list:
            return 'funcdef'
        if 'grammar' in list and 'expr' in list:
            return 'expr'
        # print >> sys.stderr, 'resolve', str(list)
        return GenericASTBuilder.resolve(self, list)

def parse(p, tokens, customize):
    p.add_custom_rules(tokens, customize)
    ast = p.parse(tokens)
    #  p.cleanup()
    return ast


def get_python_parser(version, debug_parser):
    """
    Returns parser object for Python version 2 or 3
    depending on the parameter passed.
    """
    if version < 3.0:
        import uncompyle6.parsers.parse2 as parse2
        p = parse2.Python2Parser(debug_parser)
    else:
        import uncompyle6.parsers.parse3 as parse3
        p = parse3.Python3Parser(debug_parser)
    p.version = version
    return p

def python_parser(version, co, out=sys.stdout, showasm=False,
                  parser_debug=PARSER_DEFAULT_DEBUG):
    assert iscode(co)
    from uncompyle6.scanner import get_scanner
    scanner = get_scanner(version)
    tokens, customize = scanner.disassemble(co)
    if showasm:
        for t in tokens:
            print(t)

    p = get_python_parser(version, parser_debug)
    return parse(p, tokens, customize)

if __name__ == '__main__':
    def parse_test(co):
        from uncompyl6e import PYTHON_VERSION
        ast = python_parser(PYTHON_VERSION, co, showasm=True)
        print(ast)
        return
    parse_test(parse_test.__code__)
