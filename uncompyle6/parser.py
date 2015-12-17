#  Copyright (c) 1999 John Aycock
#  Copyright (c) 2000-2002 by hartmut Goebel <h.goebel@crazy-compilers.com>
#  Copyright (c) 2005 by Dan Pascu <dan@windowmaker.org>
#  Copyright (c) 2015 Rocky Bernstein
"""
Common spark parser routines Python.
"""

from __future__ import print_function

from uncompyle6 import PYTHON3

import sys

from uncompyle6.parsers.spark import GenericASTBuilder

if PYTHON3:
    intern = sys.intern
    from collections import UserList
else:
    from UserList import UserList

class ParserError(Exception):
    def __init__(self, token, offset):
        self.token = token
        self.offset = offset

    def __str__(self):
        return "Syntax error at or near `%r' token at offset %s\n" % \
               (self.token, self.offset)

class AST(UserList):
    def __init__(self, type, kids=[]):
        self.type = intern(type)
        UserList.__init__(self, kids)

    def __getslice__(self, low, high):    return self.data[low:high]

    def __eq__(self, o):
        if isinstance(o, AST):
            return self.type == o.type \
                   and UserList.__eq__(self, o)
        else:
            return self.type == o

    def __hash__(self):            return hash(self.type)

    def __repr__(self, indent=''):
        rv = str(self.type)
        for k in self:
            rv = rv + '\n' + str(k).replace('\n', '\n   ')
        return rv

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
    '''
    Special handling for opcodes that take a variable number
    of arguments -- we add a new rule for each:

        expr ::= {expr}^n BUILD_LIST_n
        expr ::= {expr}^n BUILD_TUPLE_n
        unpack_list ::= UNPACK_LIST {expr}^n
        unpack ::= UNPACK_TUPLE {expr}^n
        unpack ::= UNPACK_SEQEUENE {expr}^n
        mkfunc ::= {expr}^n LOAD_CONST MAKE_FUNCTION_n
        mkfunc ::= {expr}^n load_closure LOAD_CONST MAKE_FUNCTION_n
        expr ::= expr {expr}^n CALL_FUNCTION_n
        expr ::= expr {expr}^n CALL_FUNCTION_VAR_n POP_TOP
        expr ::= expr {expr}^n CALL_FUNCTION_VAR_KW_n POP_TOP
        expr ::= expr {expr}^n CALL_FUNCTION_KW_n POP_TOP
    '''
    nop = lambda self, args: None

    for k, v in list(customize.items()):
        # avoid adding the same rule twice to this parser
        if k in p.customized:
            continue
        p.customized[k] = None

        # nop = lambda self, args: None

        op = k[:k.rfind('_')]
        if op in ('BUILD_LIST', 'BUILD_TUPLE', 'BUILD_SET'):
            rule = 'build_list ::= ' + 'expr '*v + k
        elif op in ('UNPACK_TUPLE', 'UNPACK_SEQUENCE'):
            rule = 'unpack ::= ' + k + ' designator'*v
        elif op == 'UNPACK_LIST':
            rule = 'unpack_list ::= ' + k + ' designator'*v
        elif op in ('DUP_TOPX', 'RAISE_VARARGS'):
            # no need to add a rule
            continue
            # rule = 'dup_topx ::= ' + 'expr '*v + k
        elif op == 'MAKE_FUNCTION':
            p.addRule('mklambda ::= %s LOAD_LAMBDA %s' %
                  ('expr '*v, k), nop)
            rule = 'mkfunc ::= %s LOAD_CONST %s' % ('expr '*v, k)
        elif op == 'MAKE_CLOSURE':
            p.addRule('mklambda ::= %s load_closure LOAD_LAMBDA %s' %
                  ('expr '*v, k), nop)
            p.addRule('genexpr ::= %s load_closure LOAD_GENEXPR %s expr GET_ITER CALL_FUNCTION_1' %
                  ('expr '*v, k), nop)
            p.addRule('setcomp ::= %s load_closure LOAD_SETCOMP %s expr GET_ITER CALL_FUNCTION_1' %
                  ('expr '*v, k), nop)
            p.addRule('dictcomp ::= %s load_closure LOAD_DICTCOMP %s expr GET_ITER CALL_FUNCTION_1' %
                  ('expr '*v, k), nop)
            rule = 'mkfunc ::= %s load_closure LOAD_CONST %s' % ('expr '*v, k)
#            rule = 'mkfunc ::= %s closure_list LOAD_CONST %s' % ('expr '*v, k)
        elif op in ('CALL_FUNCTION', 'CALL_FUNCTION_VAR',
                'CALL_FUNCTION_VAR_KW', 'CALL_FUNCTION_KW'):
            na = (v & 0xff)           # positional parameters
            nk = (v >> 8) & 0xff      # keyword parameters
            # number of apply equiv arguments:
            nak = ( len(op)-len('CALL_FUNCTION') ) // 3
            rule = 'call_function ::= expr ' + 'expr '*na + 'kwarg '*nk \
                   + 'expr ' * nak + k
        else:
            raise Exception('unknown customize token %s' % k)
        p.addRule(rule, nop)
    ast = p.parse(tokens)
#   p.cleanup()
    return ast


def get_python_parser(version):
    """
    Returns parser object for Python version 2 or 3
    depending on the parameter passed.
    """
    if version < 3.0:
        import uncompyle6.parsers.parse2 as parse2
        return parse2.Python2Parser()
    else:
        import uncompyle6.parsers.parse3 as parse3
        return parse3.Python3Parser()

def python_parser(version, co, out=sys.stdout, showasm=False):
    import inspect
    assert inspect.iscode(co)
    from uncompyle6.scanner import get_scanner
    scanner = get_scanner(version)
    tokens, customize = scanner.disassemble(co)
    # if showasm:
    #     for t in tokens:
    #         print(t)

    p = get_python_parser(version)
    return parse(p, tokens, customize)

if __name__ == '__main__':
    def parse_test(co):
        sys_version = sys.version_info.major + (sys.version_info.minor / 10.0)
        ast = python_parser(sys_version, co, showasm=True)
        print(ast)
        return
    parse_test(parse_test.__code__)
