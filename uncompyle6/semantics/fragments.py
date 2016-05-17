#  Copyright (c) 2015, 2016 by Rocky Bernstein
#  Copyright (c) 2005 by Dan Pascu <dan@windowmaker.org>
#  Copyright (c) 2000-2002 by hartmut Goebel <h.goebel@crazy-compilers.com>
#  Copyright (c) 1999 John Aycock

"""
Creates Python source code from an uncompyle6 abstract syntax tree,
and indexes fragments which can be accessed by instruction offset
address.

See the comments in pysource for information on the abstract sytax tree
and how semantic actions are written.

We add a format specifier here not used in pysource

   %x takes an argument (src, (dest...)) and copies all of the range attributes
from src to dest. For example in:


    'importstmt': ( '%|import %c%x\n', 2, (2,(0,1)), ),

node 2 range information, it in %c, is copied to nodes 0 and 1.
"""

# FIXME: DRY code with pysource

from __future__ import print_function

import re, sys

from uncompyle6 import PYTHON3
from uncompyle6.code import iscode
from uncompyle6.semantics import pysource
from uncompyle6.parser import get_python_parser
from uncompyle6 import parser
from uncompyle6.scanner import Token, Code, get_scanner

from uncompyle6.semantics.pysource import AST, INDENT_PER_LEVEL, NONE, PRECEDENCE, \
     ParserError, TABLE_DIRECT, escape, find_all_globals, find_globals, find_none, minint

if PYTHON3:
    from itertools import zip_longest
    from io import StringIO
else:
    from itertools import izip_longest as zip_longest
    from StringIO import StringIO


from spark_parser import GenericASTTraversal, GenericASTTraversalPruningException, \
     DEFAULT_DEBUG as PARSER_DEFAULT_DEBUG

from types import CodeType

from collections import namedtuple
NodeInfo = namedtuple("NodeInfo", "node start finish")
ExtractInfo = namedtuple("ExtractInfo",
                         "lineNo lineStartOffset markerLine selectedLine selectedText")

TABLE_DIRECT_FRAGMENT = {
    'importstmt': ( '%|import %c%x\n', 2, (2, (0, 1)), ),
    'importfrom': ( '%|from %[2]{pattr}%x import %c\n', (2, (0, 1)), 3),
    # FIXME: fix bugs below and add
    # 'forstmt':		( '%|for %c%x in %c:\n%+%c%-\n\n', 3, (3, (2,)), 1, 4 ),
    # 'forelsestmt':	(
    #     '%|for %c in %c%x:\n%+%c%-%|else:\n%+%c%-\n\n', 3, (3, (2,)), 1, 4, -2),
    # 'forelselaststmt':	(
    #     '%|for %c%x in %c:\n%+%c%-%|else:\n%+%c%-', 3, (3, (2,)), 1, 4, -2),
    # 'forelselaststmtl':	(
    #     '%|for %c%x in %c:\n%+%c%-%|else:\n%+%c%-\n\n', 3, (3, (2,)), 1, 4, -2),
    }

class FragmentsWalker(pysource.SourceWalker, object):
    stacked_params = ('f', 'indent', 'isLambda', '_globals')

    def __init__(self, version, scanner, showast=False,
                 debug_parser=PARSER_DEFAULT_DEBUG):
        GenericASTTraversal.__init__(self, ast=None)
        self.scanner = scanner
        params = {
            'f': StringIO(),
            'indent': '',
            }
        self.version = version
        self.p = get_python_parser(version, dict(debug_parser))
        self.showast = showast
        self.params = params
        self.param_stack = []
        self.ERROR = None
        self.prec = 100
        self.return_none = False
        self.mod_globs = set()
        self.currentclass = None
        self.classes = []
        self.pending_newlines = 0
        self.hide_internal = False

        self.offsets = {}
        self.last_finish = -1

        # Customize with our more-pervisive rules
        TABLE_DIRECT.update(TABLE_DIRECT_FRAGMENT)

    f = property(lambda s: s.params['f'],
                 lambda s, x: s.params.__setitem__('f', x),
                 lambda s: s.params.__delitem__('f'),
                 None)

    indent = property(lambda s: s.params['indent'],
                 lambda s, x: s.params.__setitem__('indent', x),
                 lambda s: s.params.__delitem__('indent'),
                 None)

    isLambda = property(lambda s: s.params['isLambda'],
                 lambda s, x: s.params.__setitem__('isLambda', x),
                 lambda s: s.params.__delitem__('isLambda'),
                 None)

    _globals = property(lambda s: s.params['_globals'],
                 lambda s, x: s.params.__setitem__('_globals', x),
                 lambda s: s.params.__delitem__('_globals'),
                 None)

    def set_pos_info(self, node, start, finish):
        if hasattr(node, 'offset'):
            self.offsets[self.name, node.offset] = \
              NodeInfo(node = node, start = start, finish = finish)

        if hasattr(node, 'parent'):
            assert node.parent != node

        node.start  = start
        node.finish = finish
        self.last_finish = finish

    def preorder(self, node=None):

        if node is None:
            node = self.ast

        start = len(self.f.getvalue())

        try:
            name = 'n_' + self.typestring(node)
            if hasattr(self, name):
                func = getattr(self, name)
                func(node)
            else:
                self.default(node)
        except GenericASTTraversalPruningException:
            # All leaf nodes, those with the offset method among others
            # seems to fit under this exception. If this is not true
            # we would need to dupllicate the below code before the
            # return outside of this block
            self.set_pos_info(node, start, len(self.f.getvalue()))
            # print self.f.getvalue()[start:]
            return

        for kid in node:
            self.preorder(kid)

        name = name + '_exit'
        if hasattr(self, name):
            func = getattr(self, name)
            func(node)
        self.set_pos_info(node, start, len(self.f.getvalue()))

        return

    def n_return_stmt(self, node):
        start = len(self.f.getvalue()) + len(self.indent)
        if self.params['isLambda']:
            self.preorder(node[0])
            if hasattr(node[-1], 'offset'):
                self.set_pos_info(node[-1], start,
                len(self.f.getvalue()))
            self.prune()
        else:
            start = len(self.f.getvalue()) + len(self.indent)
            self.write(self.indent, 'return')
            if self.return_none or node != AST('return_stmt', [AST('ret_expr', [NONE]), Token('RETURN_VALUE')]):
                self.write(' ')
                self.last_finish = len(self.f.getvalue())
                self.preorder(node[0])
                if hasattr(node[-1], 'offset'):
                    self.set_pos_info(node[-1], start, len(self.f.getvalue()))
                    pass
                pass
            else:
                for n in node:
                    self.set_pos_info(n, start, len(self.f.getvalue()))
                    pass
                pass
            self.set_pos_info(node, start, len(self.f.getvalue()))
            self.println()
            self.prune() # stop recursing

    def n_return_if_stmt(self, node):

        start = len(self.f.getvalue()) + len(self.indent)
        if self.params['isLambda']:
            node[0].parent = node
            self.preorder(node[0])
        else:
            start = len(self.f.getvalue()) + len(self.indent)
            self.write(self.indent, 'return')
            if self.return_none or node != AST('return_stmt', [AST('ret_expr', [NONE]), Token('RETURN_END_IF')]):
                self.write(' ')
                self.preorder(node[0])
                if hasattr(node[-1], 'offset'):
                    self.set_pos_info(node[-1], start, len(self.f.getvalue()))
            self.println()
        self.set_pos_info(node, start, len(self.f.getvalue()))
        self.prune() # stop recursing

    def n_yield(self, node):
        start = len(self.f.getvalue())
        self.write('yield')
        if node != AST('yield', [NONE, Token('YIELD_VALUE')]):
            self.write(' ')
            node[0].parent = node
            self.preorder(node[0])
        self.set_pos_info(node, start, len(self.f.getvalue()))
        self.prune() # stop recursing

    # In Python 3.3+ only
    def n_yield_from(self, node):
        start = len(self.f.getvalue())
        self.write('yield from')
        self.write(' ')
        node[0].parent = node
        self.preorder(node[0][0][0][0])
        self.set_pos_info(node, start, len(self.f.getvalue()))
        self.prune() # stop recursing

    def n_buildslice3(self, node):
        start = len(self.f.getvalue())
        p = self.prec
        self.prec = 100
        if node[0] != NONE:
            self.preorder(node[0])
        self.write(':')
        if node[1] != NONE:
            self.preorder(node[1])
        self.write(':')
        if node[2] != NONE:
            self.preorder(node[2])
        self.prec = p
        self.set_pos_info(node, start, len(self.f.getvalue()))
        self.prune() # stop recursing

    def n_buildslice2(self, node):
        start = len(self.f.getvalue())
        p = self.prec
        self.prec = 100
        if node[0] != NONE:
            node[0].parent = node
            self.preorder(node[0])
        self.write(':')
        if node[1] != NONE:
            node[1].parent = node
            self.preorder(node[1])
        self.prec = p
        self.set_pos_info(node, start, len(self.f.getvalue()))
        self.prune() # stop recursing

    def n_expr(self, node):
        start = len(self.f.getvalue())
        p = self.prec
        if node[0].type.startswith('binary_expr'):
            n = node[0][-1][0]
        else:
            n = node[0]
        self.prec = PRECEDENCE.get(n.type, -2)
        if n == 'LOAD_CONST' and repr(n.pattr)[0] == '-':
            n.parent = node
            self.set_pos_info(n, start, len(self.f.getvalue()))
            self.prec = 6
        if p < self.prec:
            self.write('(')
            node[0].parent = node
            self.last_finish = len(self.f.getvalue())
            self.preorder(node[0])
            self.write(')')
            self.last_finish = len(self.f.getvalue())
        else:
            node[0].parent = node
            self.preorder(node[0])
        self.prec = p
        self.set_pos_info(node, start, len(self.f.getvalue()))
        self.prune()

    def n_ret_expr(self, node):
        start = len(self.f.getvalue())
        if len(node) == 1 and node[0] == 'expr':
            node[0].parent = node
            self.n_expr(node[0])
        else:
            self.n_expr(node)
        self.set_pos_info(node, start, len(self.f.getvalue()))

    def n_binary_expr(self, node):
        start = len(self.f.getvalue())
        node[0].parent = node
        self.last_finish = len(self.f.getvalue())
        self.preorder(node[0])
        self.write(' ')
        node[-1].parent = node
        self.preorder(node[-1])
        self.write(' ')
        self.prec -= 1
        node[1].parent = node
        self.preorder(node[1])
        self.prec += 1
        self.set_pos_info(node, start, len(self.f.getvalue()))
        self.prune()

    def n_LOAD_CONST(self, node):
        start = len(self.f.getvalue())
        data = node.pattr; datatype = type(data)
        if isinstance(datatype, int) and data == minint:
            # convert to hex, since decimal representation
            # would result in 'LOAD_CONST; UNARY_NEGATIVE'
            # change:hG/2002-02-07: this was done for all negative integers
            # todo: check whether this is necessary in Python 2.1
            self.write( hex(data) )
        elif datatype is type(Ellipsis):
            self.write('...')
        elif data is None:
            # LOAD_CONST 'None' only occurs, when None is
            # implicit eg. in 'return' w/o params
            # pass
            self.write('None')
        else:
            self.write(repr(data))
        self.set_pos_info(node, start, len(self.f.getvalue()))
        # LOAD_CONST is a terminal, so stop processing/recursing early
        self.prune()

    def n_exec_stmt(self, node):
        """
        exec_stmt ::= expr exprlist DUP_TOP EXEC_STMT
        exec_stmt ::= expr exprlist EXEC_STMT
        """
        start = len(self.f.getvalue()) + len(self.indent)
        self.write(self.indent, 'exec ')
        self.preorder(node[0])
        if node[1][0] != NONE:
            sep = ' in '
            for subnode in node[1]:
                self.write(sep); sep = ", "
                self.preorder(subnode)
        self.set_pos_info(node, start, len(self.f.getvalue()))
        self.println()
        self.prune() # stop recursing

    def n_ifelsestmtr(self, node):
        if len(node[2]) != 2:
            self.default(node)

        if not (node[2][0][0][0] == 'ifstmt' and node[2][0][0][0][1][0] == 'return_if_stmts') \
                and not (node[2][0][-1][0] == 'ifstmt' and node[2][0][-1][0][1][0] == 'return_if_stmts'):
            self.default(node)
            return

        start = len(self.f.getvalue()) + len(self.indent)
        self.write(self.indent, 'if ')
        self.preorder(node[0])
        self.println(':')
        self.indentMore()
        node[1].parent = node
        self.preorder(node[1])
        self.indentLess()

        if_ret_at_end = False
        if len(node[2][0]) >= 3:
            node[2][0].parent = node
            if node[2][0][-1][0] == 'ifstmt' and node[2][0][-1][0][1][0] == 'return_if_stmts':
                if_ret_at_end = True

        past_else = False
        prev_stmt_is_if_ret = True
        for n in node[2][0]:
            if (n[0] == 'ifstmt' and n[0][1][0] == 'return_if_stmts'):
                if prev_stmt_is_if_ret:
                    n[0].type = 'elifstmt'
                prev_stmt_is_if_ret = True
            else:
                prev_stmt_is_if_ret = False
                if not past_else and not if_ret_at_end:
                    self.println(self.indent, 'else:')
                    self.indentMore()
                    past_else = True
            n.parent = node
            self.preorder(n)
        if not past_else or if_ret_at_end:
            self.println(self.indent, 'else:')
            self.indentMore()
        node[2][1].parent = node
        self.preorder(node[2][1])
        self.set_pos_info(node, start, len(self.f.getvalue()))
        self.indentLess()
        self.prune()

    def n_elifelsestmtr(self, node):
        if len(node[2]) != 2:
            self.default(node)

        for n in node[2][0]:
            if not (n[0] == 'ifstmt' and n[0][1][0] == 'return_if_stmts'):
                self.default(node)
                return

        start = len(self.f.getvalue() + self.indent)
        self.write(self.indent, 'elif ')
        node[0].parent = node
        self.preorder(node[0])
        self.println(':')
        self.indentMore()
        node[1].parent = node
        self.preorder(node[1])
        self.indentLess()

        for n in node[2][0]:
            n[0].type = 'elifstmt'
            n.parent = node
            self.preorder(n)
        self.println(self.indent, 'else:')
        self.indentMore()
        node[2][1].parent = node
        self.preorder(node[2][1])
        self.indentLess()
        self.set_pos_info(node, start, len(self.f.getvalue()))
        self.prune()

    def n_import_as(self, node):
        start = len(self.f.getvalue())
        iname = node[0].pattr

        store_import_node = node[-1][-1]
        assert store_import_node.type.startswith('STORE_')

        sname = store_import_node.pattr
        self.write(iname)
        finish = len(self.f.getvalue())
        if iname == sname or iname.startswith(sname + '.'):
            self.set_pos_info_recurse(node, start, finish)
        else:
            self.write(' as ')
            sname_start = len(self.f.getvalue())
            self.write(sname)
            finish = len(self.f.getvalue())
            for n in node[-1]:
                self.set_pos_info_recurse(n, sname_start, finish)
            self.set_pos_info(node, start, finish)
        self.prune() # stop recursing

    def n_mkfunc(self, node):
        start = len(self.f.getvalue())
        old_name = self.name
        if self.version >= 3.0:
            # LOAD_CONST code object ..
            # LOAD_CONST        'x0'  if >= 3.3
            # MAKE_FUNCTION ..
            if self.version >= 3.4:
                func_name =  node[-2].attr
                code_index = -3
            elif self.version == 3.3:
                func_name = node[-2].pattr
                code_index = -3
            else:
                func_name = node[-2].attr.co_name
                code_index = -2
            pass
        else:
            # LOAD_CONST code object ..
            # MAKE_FUNCTION ..
            func_name =   node[-2].attr.co_name
            code_index = -2
        self.write(func_name)
        self.indentMore()
        self.make_function(node, isLambda=False, code_index=code_index)
        self.name = old_name
        self.set_pos_info(node, start, len(self.f.getvalue()))
        if len(self.param_stack) > 1:
            self.write('\n\n')
        else:
            self.write('\n\n\n')
        self.indentLess()
        self.prune() # stop recursing

    def comprehension_walk(self, node, iter_index, code_index=-5):
        p = self.prec
        self.prec = 27
        if hasattr(node[code_index], 'attr'):
            # Python 2.5+ (and earlier?) does this
            code = node[code_index].attr
        else:
            if len(node[1]) > 1 and hasattr(node[1][1], 'attr'):
                # Python 3.3+ does this
                code = node[1][1].attr
            elif hasattr(node[1][0], 'attr'):
                # Python 3.2 does this
                code = node[1][0].attr
            else:
                assert False, "Can't find code for comprehension"

        assert iscode(code)
        code = Code(code, self.scanner, self.currentclass)

        ast = self.build_ast(code._tokens, code._customize)
        self.customize(code._customize)
        ast = ast[0][0][0]

        n = ast[iter_index]
        assert n == 'comp_iter'
        # find innermost node
        while n == 'comp_iter':
            n = n[0] # recurse one step
            if   n == 'comp_for':	n = n[3]
            elif n == 'comp_if':	n = n[2]
            elif n == 'comp_ifnot': n = n[2]
        assert n == 'comp_body', ast

        self.preorder(n[0])
        self.write(' for ')
        start = len(self.f.getvalue())
        designator = ast[iter_index-1]
        self.preorder(designator)
        self.set_pos_info(ast[iter_index-1], start, len(self.f.getvalue()))
        self.write(' in ')
        start = len(self.f.getvalue())
        node[-3].parent = node
        self.preorder(node[-3])
        self.set_pos_info(node[-3], start, len(self.f.getvalue()))
        start = len(self.f.getvalue())
        self.preorder(ast[iter_index])
        self.set_pos_info(iter_index, start, len(self.f.getvalue()))
        self.prec = p

    def listcomprehension_walk3(self, node, iter_index, code_index=-5):
        """List comprehensions the way they are done in Python3.
        They're more other comprehensions, e.g. set comprehensions
        See if we can combine code.
        """
        p = self.prec
        self.prec = 27
        code = node[code_index].attr

        assert iscode(code)
        # Or Code3
        code = Code(code, self.scanner, self.currentclass)

        ast = self.build_ast(code._tokens, code._customize)
        self.customize(code._customize)
        ast = ast[0][0][0][0][0]

        n = ast[iter_index]
        assert n == 'list_iter'

        # find innermost node
        while n == 'list_iter':
            n = n[0] # recurse one step
            if   n == 'list_for':
                designator = n[2]
                n = n[3]
            elif n == 'list_if':
                # FIXME: just a guess
                designator = n[1]

                n = n[2]
            elif n == 'list_if_not':
                # FIXME: just a guess
                designator = n[1]
                n = n[2]
        assert n == 'lc_body', ast

        self.preorder(n[0])
        self.write(' for ')
        start = len(self.f.getvalue())
        self.preorder(designator)
        self.set_pos_info(designator, start, len(self.f.getvalue()))
        self.write(' in ')
        start = len(self.f.getvalue())
        node[-3].parent = node
        self.preorder(node[-3])
        self.set_pos_info(node[-3], start, len(self.f.getvalue()))
        # self.preorder(ast[iter_index])
        self.prec = p

    def listcomprehension_walk2(self, node):
        """List comprehensions the way they are done in Python3.
        They're more other comprehensions, e.g. set comprehensions
        See if we can combine code.
        """
        p = self.prec
        self.prec = 27

        code = Code(node[1].attr, self.scanner, self.currentclass)
        ast = self.build_ast(code._tokens, code._customize)
        self.customize(code._customize)
        ast = ast[0][0][0][0][0]

        n = ast[1]
        collection = node[-3]
        list_if = None
        assert n == 'list_iter'

        # find innermost node
        while n == 'list_iter':
            n = n[0] # recurse one step
            if   n == 'list_for':
                designator = n[2]
                n = n[3]
            elif n in ('list_if', 'list_if_not'):
                # FIXME: just a guess
                if n[0].type == 'expr':
                    list_if = n
                else:
                    list_if = n[1]
                n = n[2]
                pass
            pass

        assert n == 'lc_body', ast

        self.preorder(n[0])
        self.write(' for ')
        start = len(self.f.getvalue())
        self.preorder(designator)
        self.set_pos_info(designator, start, len(self.f.getvalue()))
        self.write(' in ')
        start = len(self.f.getvalue())
        node[-3].parent = node
        self.preorder(collection)
        self.set_pos_info(collection, start, len(self.f.getvalue()))
        if list_if:
            start = len(self.f.getvalue())
            self.preorder(list_if)
            self.set_pos_info(list_if, start, len(self.f.getvalue()))

        self.prec = p

    def n_genexpr(self, node):
        start = len(self.f.getvalue())
        self.write('(')
        code_index = -6 if self.version > 3.0 else -5
        self.comprehension_walk(node, iter_index=3, code_index=code_index)
        self.write(')')
        self.set_pos_info(node, start, len(self.f.getvalue()))
        self.prune()

    def n_setcomp(self, node):
        start = len(self.f.getvalue())
        self.write('{')
        self.comprehension_walk(node, 4)
        self.write('}')
        self.set_pos_info(node, start, len(self.f.getvalue()))
        self.prune()

    def n_classdef(self, node):
        # class definition ('class X(A,B,C):')
        cclass = self.currentclass

        if self.version > 3.0:
            currentclass = node[1][0].pattr
            buildclass = node[0]
            if buildclass[1][0] == 'kwargs':
                subclass = buildclass[1][1].attr
                subclass_info = node[0]
            elif buildclass[1][0] == 'load_closure':
                # Python 3 with closures not functions
                load_closure = buildclass[1]
                if hasattr(load_closure[-3], 'attr'):
                    # Python 3.3 classes with closures work like this.
                    # Note have to test before 3.2 case because
                    # index -2 also has an attr.
                    subclass = load_closure[-3].attr
                elif hasattr(load_closure[-2], 'attr'):
                    # Python 3.2 works like this
                    subclass = load_closure[-2].attr
                else:
                    raise 'Internal Error n_classdef: cannot find class body'
                if hasattr(buildclass[3], '__len__'):
                    subclass_info = buildclass[3]
                elif hasattr(buildclass[2], '__len__'):
                    subclass_info = buildclass[2]
                else:
                    raise 'Internal Error n_classdef: cannot superclass name'
            else:
                subclass = buildclass[1][0].attr
                subclass_info = node[0]
        else:
            buildclass = node[0]
            build_list = buildclass[1][0]
            if hasattr(buildclass[-3][0], 'attr'):
                subclass = buildclass[-3][0].attr
                currentclass = buildclass[0].pattr
            elif hasattr(node[0][0], 'pattr'):
                subclass = buildclass[-3][1].attr
                currentclass = node[0][0].pattr
            else:
                raise 'Internal Error n_classdef: cannot find class name'

        self.write('\n\n')
        self.currentclass = str(currentclass)
        start = len(self.f.getvalue())
        self.write(self.indent, 'class ', self.currentclass)

        if self.version > 3.0:
            self.print_super_classes3(subclass_info)
        else:
            self.print_super_classes(build_list)
        self.println(':')

        # class body
        self.indentMore()
        self.build_class(subclass)
        self.indentLess()

        self.currentclass = cclass
        self.set_pos_info(node, start, len(self.f.getvalue()))
        if len(self.param_stack) > 1:
            self.write('\n\n')
        else:
            self.write('\n\n\n')

        self.prune()

    def gen_source(self, ast, name, customize, isLambda=0, returnNone=False):
        """convert AST to source code"""

        rn = self.return_none
        self.return_none = returnNone
        self.name = name
        # if code would be empty, append 'pass'
        if len(ast) == 0:
            self.println(self.indent, 'pass')
        else:
            self.customize(customize)
            self.text = self.traverse(ast, isLambda=isLambda)
        self.return_none = rn

    def build_ast(self, tokens, customize, isLambda=0, noneInNames=False):
        # assert type(tokens) == ListType
        # assert isinstance(tokens[0], Token)

        if isLambda:
            tokens.append(Token('LAMBDA_MARKER'))
            try:
                ast = parser.parse(self.p, tokens, customize)
            except (parser.ParserError, AssertionError) as e:
                raise ParserError(e, tokens)
            if self.showast:
                print(repr(ast))
            return ast

        # The bytecode for the end of the main routine has a
        # "return None". However you can't issue a "return" statement in
        # main. In the other build_ast routine we eliminate the
        # return statement instructions before parsing.
        # But here we want to keep these instructions at the expense of
        # a fully runnable Python program because we
        # my be queried about the role of one of those instructuions

        if len(tokens) >= 2 and not noneInNames:
            if tokens[-1].type == 'RETURN_VALUE':
                if tokens[-2].type != 'LOAD_CONST':
                    tokens.append(Token('RETURN_LAST'))
        if len(tokens) == 0:
            return

        # Build AST from disassembly.
        try:
            ast = parser.parse(self.p, tokens, customize)
        except (parser.ParserError, AssertionError) as e:
            raise ParserError(e, tokens)

        if self.showast:
            print(repr(ast))

        return ast

    # FIXME: we could provide another customized routine
    # that fixes up parents along a particular path to a node that
    # we are interested in.
    def fixup_parents(self, node, parent):
        """Make sure each node has a parent"""
        start, finish = 0, self.last_finish
        # We assume anything with a start has a finish.
        needs_range = not hasattr(node, 'start')

        if not hasattr(node, 'parent'):
            node.parent = parent

        for n in node:
            if needs_range and hasattr(n, 'start'):
                if n.start < start: start = n.start
                if n.finish > finish: finish = n.finish

            if hasattr(n, 'offset') and not hasattr(n, 'parent'):
                n.parent = node
            else:
                self.fixup_parents(n, node)
                pass
            pass
        if needs_range:
            node.start, node.finish = start, finish

        return

    # FIXME: revise to do *once* over the entire tree.
    # So here we should just mark that the subtree
    # needs offset adjustment.
    def fixup_offsets(self, new_start, node):
        """Adjust all offsets under node"""
        if hasattr(node, 'start'):
            node.start += new_start
            node.finish += new_start
        for n in node:
            if hasattr(n, 'offset'):
                if hasattr(n, 'start'):
                    n.start += new_start
                    n.finish += new_start
            else:
                self.fixup_offsets(new_start, n)
        return

    def set_pos_info_recurse(self, node, start, finish):
        """Set positions under node"""
        self.set_pos_info(node, start, finish)
        for n in node:
            if hasattr(n, 'offset'):
                self.set_pos_info(n, start, finish)
            else:
                self.set_pos_info_recurse(n, start, finish)
        return

    def node_append(self, before_str, node_text, node):
        self.write(before_str)
        self.last_finish = len(self.f.getvalue())
        self.fixup_offsets(self.last_finish, node)
        self.write(node_text)
        self.last_finish = len(self.f.getvalue())

    # FIXME: duplicated from pysource, since we don't find self.params
    def traverse(self, node, indent=None, isLambda=0):
        '''Buulds up fragment which can be used inside a larger
        block of code'''

        self.param_stack.append(self.params)
        if indent is None: indent = self.indent
        p = self.pending_newlines
        self.pending_newlines = 0
        self.params = {
            '_globals': {},
            'f': StringIO(),
            'indent': indent,
            'isLambda': isLambda,
            }
        self.preorder(node)
        self.f.write('\n'*self.pending_newlines)

        text = self.f.getvalue()
        self.last_finish = len(text)

        self.params = self.param_stack.pop()
        self.pending_newlines = p

        return text

    def extract_node_info(self, nodeInfo):
        # XXX debug
        # print('-' * 30)
        # node = nodeInfo.node
        # print(node)
        # if hasattr(node, 'parent'):
        #     print('~' * 30)
        #     print(node.parent)
        # else:
        #     print("No parent")
        # print('-' * 30)

        start, finish = (nodeInfo.start, nodeInfo.finish)
        text = self.text

        # Ignore trailing blanks
        match = re.search(r'\n+$', text[start:])
        if match:
            text = text[:-len(match.group(0))]

        # Ignore leading blanks
        match = re.search(r'\s*[^ \t\n]', text[start:])
        if match:
            start += len(match.group(0))-1

        at_end = False
        if start  >= finish:
            at_end = True
            selectedText = text
        else:
            selectedText = text[start:finish]

        # Compute offsets relative to the beginning of the
        # line rather than the beinning of the text
        try:
            lineStart = text[:start].rindex("\n") + 1
        except ValueError:
            lineStart = 0
        adjustedStart = start - lineStart

        # If selected text is greater than a single line
        # just show the first line plus elipses.
        lines = selectedText.split("\n")
        if len(lines) > 1:
            adjustedEnd =  len(lines[0]) -  adjustedStart
            selectedText = lines[0] + " ...\n" + lines[-1]
        else:
            adjustedEnd =  len(selectedText)

        if at_end:
            markerLine = (' ' * len(lines[-1])) + '^'
        else:
            markerLine = ((' ' * adjustedStart) +
                          ('-' * adjustedEnd))

        elided = False
        if len(lines) > 1 and not at_end:
            elided = True
            markerLine += ' ...'

        # Get line that the selected text is in and
        # get a line count for that.
        try:
            lineEnd = lineStart + text[lineStart+1:].index("\n") - 1
        except ValueError:
            lineEnd = len(text)

        lines = text[:lineEnd].split("\n")

        selectedLine = text[lineStart:lineEnd+2]

        if elided: selectedLine += ' ...'

        return ExtractInfo(lineNo = len(lines), lineStartOffset = lineStart,
                           markerLine = markerLine,
                           selectedLine = selectedLine,
                           selectedText = selectedText)

    def extract_line_info(self, name, offset):
        if (name, offset) not in list(self.offsets.keys()):
            return None
        return self.extract_node_info(self.offsets[name, offset])

    def extract_parent_info(self, node):
        if not hasattr(node, 'parent'):
            return None, None
        p = node.parent
        orig_parent = p
        # If we can get different text, use that as the parent,
        # otherwise we'll use the immeditate parent
        while (p and (hasattr(p, 'parent') and
                    p.start == node.start and p.finish == node.finish)):
            assert p != node
            node = p
            p = p.parent
        if p is None: p = orig_parent
        return self.extract_node_info(p), p

    def print_super_classes(self, node):
        if not (node == 'build_list'):
            return

        start = len(self.f.getvalue())
        self.write('(')
        line_separator = ', '
        sep = ''
        for elem in node[:-1]:
            value = self.traverse(elem)
            self.node_append(sep, value, elem)
            # self.write(sep, value)
            sep = line_separator

        self.write(')')
        self.set_pos_info(node, start, len(self.f.getvalue()))

    def print_super_classes3(self, node):

        # FIXME: wrap superclasses onto a node
        # as a custom rule
        start = len(self.f.getvalue())
        n = len(node)-1
        assert node[n].type.startswith('CALL_FUNCTION')

        for i in range(n-2, 0, -1):
            if not node[i].type in ['expr', 'LOAD_CLASSNAME']:
                break
            pass

        if i == n-2:
            return
        self.write('(')
        line_separator = ', '
        sep = ''
        i += 1
        while i < n:
            value = self.traverse(node[i])
            self.node_append(sep, value, node[i])
            i += 1
            self.write(sep, value)
            sep = line_separator

        self.write(')')
        self.set_pos_info(node, start, len(self.f.getvalue()))

    def n_mapexpr(self, node):
        """
        prettyprint a mapexpr
        'mapexpr' is something like k = {'a': 1, 'b': 42 }"
        """
        p = self.prec
        self.prec = 100

        self.indentMore(INDENT_PER_LEVEL)
        line_seperator = ',\n' + self.indent
        sep = INDENT_PER_LEVEL[:-1]
        start = len(self.f.getvalue())
        self.write('{')

        if self.version > 3.0:
            if node[0].type.startswith('kvlist'):
                # Python 3.5+ style key/value list in mapexpr
                kv_node = node[0]
                l = list(kv_node)
                i = 0
                while i < len(l):
                    l[1].parent = kv_node
                    l[i+1].parent = kv_node
                    name = self.traverse(l[i], indent='')
                    value = self.traverse(l[i+1], indent=self.indent+(len(name)+2)*' ')
                    self.write(sep, name, ': ', value)
                    sep = line_seperator
                    i += 2
                    pass
                pass
            elif node[1].type.startswith('kvlist'):
                # Python 3.0..3.4 style key/value list in mapexpr
                kv_node = node[1]
                l = list(kv_node)
                if len(l) > 0 and l[0].type == 'kv3':
                    # Python 3.2 does this
                    kv_node = node[1][0]
                    l = list(kv_node)
                i = 0
                while i < len(l):
                    l[1].parent = kv_node
                    l[i+1].parent = kv_node
                    name = self.traverse(l[i+1], indent='')
                    value = self.traverse(l[i], indent=self.indent+(len(name)+2)*' ')
                    self.write(sep, name, ': ', value)
                    sep = line_seperator
                    i += 3
                    pass
                pass
            pass
        else:
            # Python 2 style kvlist
            assert node[-1] == 'kvlist'
            kv_node = node[-1] # goto kvlist

            for kv in kv_node:
                assert kv in ('kv', 'kv2', 'kv3')
                # kv ::= DUP_TOP expr ROT_TWO expr STORE_SUBSCR
                # kv2 ::= DUP_TOP expr expr ROT_THREE STORE_SUBSCR
                # kv3 ::= expr expr STORE_MAP
                if kv == 'kv':
                    name = self.traverse(kv[-2], indent='')
                    kv[1].parent = kv_node
                    value = self.traverse(kv[1], indent=self.indent+(len(name)+2)*' ')
                elif kv == 'kv2':
                    name = self.traverse(kv[1], indent='')
                    kv[-3].parent = kv_node
                    value = self.traverse(kv[-3], indent=self.indent+(len(name)+2)*' ')
                elif kv == 'kv3':
                    name = self.traverse(kv[-2], indent='')
                    kv[0].parent = kv_node
                    value = self.traverse(kv[0], indent=self.indent+(len(name)+2)*' ')
                self.write(sep, name, ': ', value)
                sep = line_seperator
        self.write('}')
        finish = len(self.f.getvalue())
        for n in node:
            n.parent = node
            self.set_pos_info(n, start, finish)
        self.set_pos_info(node, start, finish)
        self.indentLess(INDENT_PER_LEVEL)
        self.prec = p
        self.prune()

    def n_build_list(self, node):
        """
        prettyprint a list or tuple
        """
        p = self.prec
        self.prec = 100
        n = node.pop()
        lastnode = n.type
        start = len(self.f.getvalue())
        if lastnode.startswith('BUILD_LIST'):
            self.write('['); endchar = ']'
        elif lastnode.startswith('BUILD_TUPLE'):
            self.write('('); endchar = ')'
        elif lastnode.startswith('BUILD_SET'):
            self.write('{'); endchar = '}'
        elif lastnode.startswith('ROT_TWO'):
            self.write('('); endchar = ')'
        else:
            raise RuntimeError('Internal Error: n_build_list expects list or tuple')

        flat_elems = []
        for elem in node:
            if elem == 'expr1024':
                for subelem in elem:
                        for subsubelem in subelem:
                            flat_elems.append(subsubelem)
            elif elem == 'expr32':
                for subelem in elem:
                    flat_elems.append(subelem)
            else:
                flat_elems.append(elem)

        self.indentMore(INDENT_PER_LEVEL)
        if len(node) > 3:
            line_separator = ',\n' + self.indent
        else:
            line_separator = ', '
        sep = INDENT_PER_LEVEL[:-1]

        # FIXME:
        # if flat_elems > some_number, then group
        # do automatic wrapping
        for elem in flat_elems:
            if (elem == 'ROT_THREE'):
                continue

            assert elem == 'expr'
            value = self.traverse(elem)
            self.node_append(sep, value, elem)
            sep = line_separator
        if len(node) == 1 and lastnode.startswith('BUILD_TUPLE'):
            self.write(',')
        self.write(endchar)
        finish = len(self.f.getvalue())
        n.parent = node.parent
        self.set_pos_info(n, start, finish)
        self.set_pos_info(node, start, finish)
        self.indentLess(INDENT_PER_LEVEL)
        self.prec = p
        self.prune()

    def engine(self, entry, startnode):
        """The format template interpetation engine.  See the comment at the
        beginning of this module for the how we interpret format specifications such as
        %c, %C, and so on.
        """

        # print("-----")
        # print(startnode)
        # print(entry[0])
        # print('======')

        startnode_start = len(self.f.getvalue())

        fmt = entry[0]
        arg = 1
        i = 0
        lastC = -1

        m = escape.search(fmt)
        while m:
            i = m.end()
            self.write(m.group('prefix'))

            typ = m.group('type') or '{'
            node = startnode
            try:
                if m.group('child'):
                    node = node[int(m.group('child'))]
                    node.parent = startnode
            except:
                print(node.__dict__)
                raise

            if typ == '%':
                start = len(self.f.getvalue())
                self.write('%')
                self.set_pos_info(node, start, len(self.f.getvalue()))

            elif typ == '+': self.indentMore()
            elif typ == '-': self.indentLess()
            elif typ == '|': self.write(self.indent)
            # no longer used, since BUILD_TUPLE_n is pretty printed:
            elif typ == ',':
                if lastC == 1:
                    self.write(',')
            elif typ == 'c':
                start = len(self.f.getvalue())
                self.preorder(node[entry[arg]])
                finish = len(self.f.getvalue())

                # FIXME rocky: figure out how to get this to be table driven
                # for loops have two positions that correspond to a single text
                # location. In "for i in ..." there is the initialization "i" code as well
                # as the iteration code with "i"
                match = re.search(r'^for', startnode.type)
                if match and entry[arg] == 3:
                    self.set_pos_info(node[0], start, finish)
                    for n in node[2]:
                        self.set_pos_info(n, start, finish)

                self.set_pos_info(node, start, finish)
                arg += 1
            elif typ == 'p':
                p = self.prec
                (index, self.prec) = entry[arg]
                node[index].parent = node
                start = len(self.f.getvalue())
                self.preorder(node[index])
                self.set_pos_info(node, start, len(self.f.getvalue()))
                self.prec = p
                arg += 1
            elif typ == 'C':
                low, high, sep = entry[arg]
                lastC = remaining = len(node[low:high])
                start = len(self.f.getvalue())
                for subnode in node[low:high]:
                    self.preorder(subnode)
                    remaining -= 1
                    if remaining > 0:
                        self.write(sep)

                self.set_pos_info(node, start, len(self.f.getvalue()))
                arg += 1
            elif typ == 'x':
                assert isinstance(entry[arg], tuple)
                src, dest = entry[arg]
                for n in dest:
                    self.set_pos_info(node[n], node[src].start, node[src].finish)
                arg += 1
            elif typ == 'P':
                p = self.prec
                low, high, sep, self.prec = entry[arg]
                lastC = remaining = len(node[low:high])
                start = self.last_finish
                for subnode in node[low:high]:
                    self.preorder(subnode)
                    remaining -= 1
                    if remaining > 0:
                        self.write(sep)
                self.prec = p
                arg += 1

            elif typ == '{':
                d = node.__dict__
                expr = m.group('expr')
                try:
                    start = len(self.f.getvalue())
                    self.write(eval(expr, d, d))
                    self.set_pos_info(node, start, len(self.f.getvalue()))
                except:
                    print(node)
                    raise
            m = escape.search(fmt, i)
            if hasattr(node, 'offset') and (self.name, node.offset) not in self.offsets:
                print("Type %s of node %s has an offset %d" % (typ, node, node.offset))
                pass
            pass

        self.write(fmt[i:])
        self.set_pos_info(startnode, startnode_start, len(self.f.getvalue()))

        # FIXME rocky: figure out how to get these casess to be table driven.
        #
        # 1. for loops. For loops have two positions that correspond to a single text
        # location. In "for i in ..." there is the initialization "i" code as well
        # as the iteration code with "i".  A "copy" spec like %X3,3 - copy parame
        # 3 to param 2 would work
        #
        # 2. subroutine calls. It the last op is the call and for purposes of printing
        # we don't need to print anything special there. However it encompases the
        # entire string of the node fn(...)
        match = re.search(r'^try', startnode.type)
        if match:
            self.set_pos_info(node[0], startnode_start, startnode_start+len("try:"))
            self.set_pos_info(node[2], node[3].finish, node[3].finish)
        else:
            match = re.search(r'^call_function', startnode.type)
            if match:
                last_node = startnode[-1]
                # import traceback; traceback.print_stack()
                self.set_pos_info(last_node, startnode_start, self.last_finish)
        return

    def make_function(self, node, isLambda, nested=1, code_index=-2):
        """Dump function defintion, doc string, and function body."""

        def build_param(ast, name, default):
            """build parameters:
                - handle defaults
                - handle format tuple parameters
            """
            if self.version < 3.0:
                # if formal parameter is a tuple, the paramater name
                # starts with a dot (eg. '.1', '.2')
                if name.startswith('.'):
                    # replace the name with the tuple-string
                    name = self.get_tuple_parameter(ast, name)
                    pass
                pass

            if default:
                if self.showast:
                    print()
                    print('--', name)
                    print(default)
                    print('--')
                    pass
                result = '%s=' % name
                old_last_finish = self.last_finish
                self.last_finish = len(result)
                value = self.traverse(default, indent='')
                self.last_finish = old_last_finish
                result += value
                if result[-2:] == '= ':	# default was 'LOAD_CONST None'
                    result += 'None'
                return result
            else:
                return name

        # node[-1] == MAKE_FUNCTION_n

        args_node = node[-1]
        if isinstance(args_node.attr, tuple):
            defparams = node[:args_node.attr[0]]
            pos_args, kw_args, annotate_args  = args_node.attr
        else:
            defparams = node[:args_node.attr]
            kw_args, annotate_args  = (0, 0)
            pos_args = args_node.attr
            pass

        code = node[code_index].attr

        assert iscode(code)
        code = Code(code, self.scanner, self.currentclass)

        # add defaults values to parameter names
        argc = code.co_argcount
        paramnames = list(code.co_varnames[:argc])

        # defaults are for last n parameters, thus reverse
        paramnames.reverse(); defparams.reverse()

        try:
            ast = self.build_ast(code._tokens,
                                 code._customize,
                                 isLambda = isLambda,
                                 noneInNames = ('None' in code.co_names))
        except ParserError as p:
            self.write(str(p))
            self.ERROR = p
            return

        # build parameters

        params = [build_param(ast, name, default) for
                  name, default in zip_longest(paramnames, defparams, fillvalue=None)]

        params.reverse() # back to correct order

        if 4 & code.co_flags:	# flag 2 -> variable number of args
            params.append('*%s' % code.co_varnames[argc])
            argc += 1
        if 8 & code.co_flags:	# flag 3 -> keyword args
            params.append('**%s' % code.co_varnames[argc])
            argc += 1

        # dump parameter list (with default values)
        indent = self.indent
        if isLambda:
            self.write("lambda ", ", ".join(params))
        else:
            self.write("(", ", ".join(params))
            # self.println(indent, '#flags:\t', int(code.co_flags))

        if kw_args > 0:
            if argc > 0:
                self.write(", *, ")
            else:
                self.write("*, ")
            for n in node:
                if n == 'pos_arg':
                    continue
                self.preorder(n)
                break
            pass

        if isLambda:
            self.write(": ")
        else:
            self.println("):")

        if len(code.co_consts)>0 and code.co_consts[0] is not None and not isLambda: # ugly
            # docstring exists, dump it
            self.print_docstring(indent, code.co_consts[0])

        code._tokens = None # save memory
        assert ast == 'stmts'

        all_globals = find_all_globals(ast, set())
        for g in ((all_globals & self.mod_globs) | find_globals(ast, set())):
            self.println(self.indent, 'global ', g)
        self.mod_globs -= all_globals
        rn = ('None' in code.co_names) and not find_none(ast)
        self.gen_source(ast, code.co_name, code._customize, isLambda=isLambda,
                          returnNone=rn)
        code._tokens = None; code._customize = None # save memory

    pass

def deparse_code(version, co, out=StringIO(), showasm=False, showast=False,
                 showgrammar=False):

    assert iscode(co)
    # store final output stream for case of error
    scanner = get_scanner(version)

    tokens, customize = scanner.disassemble(co)

    tokens, customize = scanner.disassemble(co)
    if showasm:
        for t in tokens:
            print(t)

    debug_parser = dict(PARSER_DEFAULT_DEBUG)
    if showgrammar:
        debug_parser['reduce'] = showgrammar
        debug_parser['errorstack'] = True

    #  Build AST from disassembly.
    # deparsed = pysource.FragmentsWalker(out, scanner, showast=showast)
    deparsed = FragmentsWalker(version, scanner, showast=showast, debug_parser=debug_parser)

    deparsed.ast = deparsed.build_ast(tokens, customize)

    assert deparsed.ast == 'stmts', 'Should have parsed grammar start'

    del tokens # save memory

    # convert leading '__doc__ = "..." into doc string
    assert deparsed.ast == 'stmts'
    deparsed.mod_globs = pysource.find_globals(deparsed.ast, set())

    # Just when you think we've forgotten about what we
    # were supposed to to: Generate source from AST!
    deparsed.gen_source(deparsed.ast, co.co_name, customize)

    deparsed.set_pos_info(deparsed.ast, 0, len(deparsed.text))
    deparsed.fixup_parents(deparsed.ast, None)

    for g in deparsed.mod_globs:
        deparsed.write('# global %s ## Warning: Unused global' % g)
    if deparsed.ERROR:
        raise deparsed.ERROR

    return deparsed

if __name__ == '__main__':

    def deparse_test(co):
        sys_version = sys.version_info.major + (sys.version_info.minor / 10.0)
        walk = deparse_code(sys_version, co, showasm=False, showast=False,
                            showgrammar=False)
        print("deparsed source")
        print(walk.text, "\n")
        print('------------------------')
        for name, offset in sorted(walk.offsets.keys(),
                                   key=lambda x: str(x[0])):
            print("name %s, offset %s" % (name, offset))
            nodeInfo = walk.offsets[name, offset]
            node = nodeInfo.node
            extractInfo = walk.extract_node_info(node)
            print("code: %s" % node.type)
            # print extractInfo
            print(extractInfo.selectedText)
            print(extractInfo.selectedLine)
            print(extractInfo.markerLine)
            extractInfo, p = walk.extract_parent_info(node)
            if extractInfo:
                print("Contained in...")
                print(extractInfo.selectedLine)
                print(extractInfo.markerLine)
                print("code: %s" % p.type)
                print('=' * 40)
                pass
            pass
        return

    def get_code_for_fn(fn):
        return fn.__code__

    def gcd(a, b):
        from os import path
        if a > b:
            (a, b) = (b, a)
            pass

        if a <= 0:
            return None
        if a == 1 or a == b:
            return a
        return gcd(b-a, a)

    # check_args(['3', '5'])
    deparse_test(get_code_for_fn(gcd))
    # deparse_test(get_code_for_fn(gcd))
    # deparse_test(get_code_for_fn(FragmentsWalker.fixup_offsets))
    # deparse_test(inspect.currentframe().f_code)
