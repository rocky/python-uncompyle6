"""
  Deparsing saving text fragment information indexed by offset

  Copyright (c) 1999 John Aycock
  Copyright (c) 2000-2002 by hartmut Goebel <h.goebel@crazy-compilers.com>
  Copyright (c) 2005 by Dan Pascu <dan@windowmaker.org>
  Copyright (c) 2015 by Rocky Bernstein

  See main module for license.

  Decompilation (walking AST)

  All table-driven. (rocky: well, mostly. I need to add more format
  specifiers for say duplicating info from one node to another.)

  Step 1 determines a table (T) and a path to a
  table key (K) from the node type (N) (other nodes are shown as O):

         N                  N               N&K
     / | ... \          / | ... \        / | ... \
    O  O      O        O  O      K      O  O      O
              |
              K

  MAP_R0 (TABLE_R0)  MAP_R (TABLE_R)  MAP_DIRECT (TABLE_DIRECT)

  The default is a direct mapping.  The key K is then extracted from the
  subtree and used to find a table entry T[K], if any.  The result is a
  format string and arguments (a la printf()) for the formatting engine.
  Escapes in the format string are:

    %c  evaluate N[A] recursively*
    %C  evaluate N[A[0]]..N[A[1]-1] recursively, separate by A[2]*
    %P  same as %C but sets operator precedence
    %,  print ',' if last %C only printed one item (for tuples--unused)
    %|  tab to current indentation level
    %+ increase current indentation level
    %- decrease current indentation level
    %{...} evaluate ... in context of N
    %% literal '%'
    %p evaluate N setting precedence


  * indicates an argument (A) required.

  The '%' may optionally be followed by a number (C) in square brackets, which
  makes the engine walk down to N[C] before evaluating the escape code.
"""

from __future__ import print_function

from uncompyle6 import walker
from uncompyle6.walker import escape, PRECEDENCE, minint
from uncompyle6.walker import AST, NONE, find_all_globals
from uncompyle6.walker import find_globals, find_none, INDENT_PER_LEVEL
from uncompyle6.walker import ParserError
from uncompyle6 import parser

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

import sys, inspect, types, re


# FIXME: remove uncompyle dups
# from uncompyle6.walker import find_all_globals, find_globals, find_none
from uncompyle6.spark import GenericASTTraversal
from uncompyle6.spark import GenericASTTraversalPruningException
from types import CodeType

try:
    from uncompyle6.Scanner import Token, Code
    older_uncompyle = True
except ImportError:
    from uncompyle6.scanner import Token, Code
    older_uncompyle = False

from collections import namedtuple
NodeInfo = namedtuple("NodeInfo", "node start finish")
ExtractInfo = namedtuple("ExtractInfo",
                         "lineNo lineStartOffset markerLine selectedLine selectedText")

class Traverser(walker.Walker, object):
    stacked_params = ('f', 'indent', 'isLambda', '_globals')

    def __init__(self, scanner, showast=0):
        GenericASTTraversal.__init__(self, ast=None)
        self.scanner = scanner
        params = {'f': StringIO(), 'indent': '', }
        self.showast = showast
        self.__params = params
        self.__param_stack = []
        self.ERROR = None
        self.prec = 100
        self.return_none = False
        self.mod_globs = set()
        self.currentclass = None
        self.pending_newlines = 0

        self.offsets = {}
        self.last_finish = -1

    f = property(lambda s: s.__params['f'],
                 lambda s, x: s.__params.__setitem__('f', x),
                 lambda s: s.__params.__delitem__('f'),
                 None)

    indent = property(lambda s: s.__params['indent'],
                 lambda s, x: s.__params.__setitem__('indent', x),
                 lambda s: s.__params.__delitem__('indent'),
                 None)

    isLambda = property(lambda s: s.__params['isLambda'],
                 lambda s, x: s.__params.__setitem__('isLambda', x),
                 lambda s: s.__params.__delitem__('isLambda'),
                 None)

    _globals = property(lambda s: s.__params['_globals'],
                 lambda s, x: s.__params.__setitem__('_globals', x),
                 lambda s: s.__params.__delitem__('_globals'),
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
        if self.__params['isLambda']:
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
            self.print_()
            self.prune() # stop recursing

    def n_return_if_stmt(self, node):

        start = len(self.f.getvalue()) + len(self.indent)
        if self.__params['isLambda']:
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
            self.print_()
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
        self.prec = PRECEDENCE.get(n, -2)
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
        self.print_()
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
        self.print_(':')
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
                    self.print_(self.indent, 'else:')
                    self.indentMore()
                    past_else = True
            n.parent = node
            self.preorder(n)
        if not past_else or if_ret_at_end:
            self.print_(self.indent, 'else:')
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
        self.print_(':')
        self.indentMore()
        node[1].parent = node
        self.preorder(node[1])
        self.indentLess()

        for n in node[2][0]:
            n[0].type = 'elifstmt'
            n.parent = node
            self.preorder(n)
        self.print_(self.indent, 'else:')
        self.indentMore()
        node[2][1].parent = node
        self.preorder(node[2][1])
        self.indentLess()
        self.set_pos_info(node, start, len(self.f.getvalue()))
        self.prune()

    def n_import_as(self, node):
        start = len(self.f.getvalue())
        iname = node[0].pattr
        assert node[-1][-1].type.startswith('STORE_')
        sname = node[-1][-1].pattr # assume one of STORE_.... here
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
        self.name = node[-2].attr.co_name # code.co_name
        self.write(self.name)
        self.indentMore()
        self.make_function(node, isLambda=0)
        self.name = old_name
        self.set_pos_info(node, start, len(self.f.getvalue()))
        if len(self.__param_stack) > 1:
            self.write('\n\n')
        else:
            self.write('\n\n\n')
        self.indentLess()
        self.prune() # stop recursing

    def comprehension_walk(self, node, iter_index):
        p = self.prec
        self.prec = 27
        code = node[-5].attr

        assert isinstance(code, types.CodeType)
        code = Code(code, self.scanner, self.currentclass)
        # assert isinstance(code, Code)

        ast = self.build_ast_d(code._tokens, code._customize)
        self.customize(code._customize)
        ast = ast[0][0][0]

        n = ast[iter_index]
        assert n == 'comp_iter'
        # find innerst node
        while n == 'comp_iter':
            n = n[0] # recurse one step
            if   n == 'comp_for':	n = n[3]
            elif n == 'comp_if':	n = n[2]
            elif n == 'comp_ifnot': n = n[2]
        assert n == 'comp_body', ast

        self.preorder(n[0])
        self.write(' for ')
        start = len(self.f.getvalue())
        self.preorder(ast[iter_index-1])
        self.set_pos_info(node, start, len(self.f.getvalue()))
        self.write(' in ')
        start = len(self.f.getvalue())
        node[-3].parent = node
        self.preorder(node[-3])
        self.set_pos_info(node, start, len(self.f.getvalue()))
        self.preorder(ast[iter_index])
        self.prec = p

    def n_genexpr(self, node):
        start = len(self.f.getvalue())
        self.write('(')
        self.comprehension_walk(node, 3)
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
        self.currentclass = str(node[0].pattr)

        self.write('\n\n')
        start = len(self.f.getvalue())
        self.write(self.indent, 'class ', self.currentclass)
        self.print_super_classes(node)
        self.print_(':')

        # class body
        self.indentMore()
        self.build_class(node[2][-2].attr)
        self.indentLess()

        self.currentclass = cclass
        self.set_pos_info(node, start, len(self.f.getvalue()))
        if len(self.__param_stack) > 1:
            self.write('\n\n')
        else:
            self.write('\n\n\n')

        self.prune()

    def gen_source_d(self, ast, name, customize, isLambda=0, returnNone=False):
        """convert AST to source code"""

        rn = self.return_none
        self.return_none = returnNone
        self.name = name
        # if code would be empty, append 'pass'
        if len(ast) == 0:
            self.print_(self.indent, 'pass')
        else:
            self.customize(customize)
            self.text = self.traverse(ast, isLambda=isLambda)
        self.return_none = rn

    def build_ast_d(self, tokens, customize, isLambda=0, noneInNames=False):
        # assert type(tokens) == ListType
        # assert isinstance(tokens[0], Token)

        if isLambda:
            tokens.append(Token('LAMBDA_MARKER'))
            try:
                ast = parser.parse(tokens, customize)
            except parser.ParserError as e:
                raise ParserError(e, tokens)
            if self.showast:
                print(repr(ast))
            return ast

        if len(tokens) >= 2 and not noneInNames:
            if tokens[-1] == Token('RETURN_VALUE'):
                if tokens[-2] != Token('LOAD_CONST'):
                    tokens.append(Token('RETURN_LAST'))
        if len(tokens) == 0:
            return

        # Build AST from disassembly.
        try:
            ast = parser.parse(tokens, customize)
        except parser.ParserError as e:
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

    # FIXME; below duplicated the code, since we don't find self.__params
    def traverse(self, node, indent=None, isLambda=0):
        '''Buulds up fragment which can be used inside a larger
        block of code'''

        self.__param_stack.append(self.__params)
        if indent is None: indent = self.indent
        p = self.pending_newlines
        self.pending_newlines = 0
        self.__params = {
            '_globals': {},
            'f': StringIO(),
            'indent': indent,
            'isLambda': isLambda,
            }
        self.preorder(node)
        self.f.write('\n'*self.pending_newlines)

        text = self.f.getvalue()
        self.last_finish = len(text)

        self.__params = self.__param_stack.pop()
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
        node[1][0].parent = node
        node = node[1][0]
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

    def n_mapexpr(self, node):
        """
        prettyprint a mapexpr
        'mapexpr' is something like k = {'a': 1, 'b': 42 }"
        """
        p = self.prec
        self.prec = 100
        assert node[-1] == 'kvlist'
        kv_node = node[-1] # goto kvlist

        self.indentMore(INDENT_PER_LEVEL)
        line_seperator = ',\n' + self.indent
        sep = INDENT_PER_LEVEL[:-1]
        start = len(self.f.getvalue())
        self.write('{')
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

        self.indentMore(INDENT_PER_LEVEL)
        if len(node) > 3:
            line_separator = ',\n' + self.indent
        else:
            line_separator = ', '
        sep = INDENT_PER_LEVEL[:-1]
        for elem in node:
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
        '''The format template interpetation engine.  See the comment at the
        beginning of this module for the how we interpret format specifications such as
        %c, %C, and so on.
        '''

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

    def make_function(self, node, isLambda, nested=1):
        """Dump function defintion, doc string, and function body."""

        def build_param(ast, name, default):
            """build parameters:
                - handle defaults
                - handle format tuple parameters
            """
            # if formal parameter is a tuple, the paramater name
            # starts with a dot (eg. '.1', '.2')
            if name.startswith('.'):
                # replace the name with the tuple-string
                name = self.get_tuple_parameter(ast, name)

            if default:
                if self.showast:
                    print('--', name)
                    print(default)
                    print('--')
                    pass
                result = '%s = ' % name
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

        defparams = node[:node[-1].attr] # node[-1] == MAKE_xxx_n
        code = node[-2].attr

        assert type(code) == CodeType
        code = Code(code, self.scanner, self.currentclass)
        # assert isinstance(code, Code)

        # add defaults values to parameter names
        argc = code.co_argcount
        paramnames = list(code.co_varnames[:argc])

        # defaults are for last n parameters, thus reverse
        paramnames.reverse(); defparams.reverse()

        try:
            ast = self.build_ast_d(code._tokens,
                                   code._customize,
                                   isLambda = isLambda,
                                   noneInNames = ('None' in code.co_names))
        except ParserError as p:
            self.write( str(p))
            self.ERROR = p
            return

        # build parameters

        # This would be a nicer piece of code, but I can't get this to work
        #  now, have to find a usable lambda constuct  hG/2000-09-05
        # params = map(lambda name, default: build_param(ast, name, default),
        # 	     paramnames, defparams)
        params = []
        for name, default in map(lambda a, b: (a, b), paramnames, defparams):
            params.append( build_param(ast, name, default) )

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
            self.write("lambda ", ", ".join(params), ": ")
        else:
            self.print_("(", ", ".join(params), "):")
            # self.print_(indent, '#flags:\t', int(code.co_flags))

        if len(code.co_consts)>0 and code.co_consts[0] is not None and not isLambda: # ugly
            # docstring exists, dump it
            self.print_docstring(indent, code.co_consts[0])

        code._tokens = None # save memory
        assert ast == 'stmts'

        all_globals = find_all_globals(ast, set())
        for g in ((all_globals & self.mod_globs) | find_globals(ast, set())):
            self.print_(self.indent, 'global ', g)
        self.mod_globs -= all_globals
        rn = ('None' in code.co_names) and not find_none(ast)
        self.gen_source_d(ast, code.co_name, code._customize, isLambda=isLambda,
                          returnNone=rn)
        code._tokens = None; code._customize = None # save memory

    pass

def deparse(version, co, out=StringIO(), showasm=0, showast=0):
    assert isinstance(co, types.CodeType)
    # store final output stream for case of error
    __real_out = out or sys.stdout
    try:
        import uncompyle6.Scanner as scan
        scanner = scan.Scanner(version)
    except ImportError:
        if version == 2.5:
            import uncompyle6.scanners.scanner25 as scan
            scanner = scan.Scanner25()
        elif version == 2.6:
            import uncompyle6.scanners.scanner26 as scan
            scanner = scan.Scanner26()
        elif version == 2.7:
            import uncompyle6.scanners.scanner27 as scan
            scanner = scan.Scanner27()
        elif version == 3.2:
            import uncompyle6.scanners.scanner34 as scan
            scanner = scan.Scanner32()
        elif version == 3.4:
            import uncompyle6.scanners.scanner34 as scan
            scanner = scan.Scanner34()

    scanner.setShowAsm(showasm, out)
    tokens, customize = scanner.disassemble(co)

    #  Build AST from disassembly.
    # walk = walker.Walker(out, scanner, showast=showast)
    walk = Traverser(scanner, showast=showast)

    try:
        if older_uncompyle:
            walk.ast = walk.build_ast_d(tokens, customize)
        else:
            walk.ast = walk.build_ast_d(tokens, customize)
    except walker.ParserError as e :  # parser failed, dump disassembly
        print(e, file=__real_out)
        raise

    del tokens # save memory

    # convert leading '__doc__ = "..." into doc string
    assert walk.ast == 'stmts'
    walk.mod_globs = walker.find_globals(walk.ast, set())
    walk.gen_source_d(walk.ast, co.co_name, customize)
    walk.set_pos_info(walk.ast, 0, len(walk.text))
    walk.fixup_parents(walk.ast, None)

    for g in walk.mod_globs:
        walk.write('global %s ## Warning: Unused global' % g)
    if walk.ERROR:
        raise walk.ERROR

    return walk

if __name__ == '__main__':

    def deparse_test(co):
        sys_version = sys.version_info.major + (sys.version_info.minor / 10.0)
        walk = deparse(sys_version, co, showasm=1, showast=1)
        print("deparsed source")
        print(walk.text, "\n")
        print('------------------------')
        for name, offset in sorted(walk.offsets.keys()):
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

    def foo(a, **options):
        def bar(a, b=1, c=2):
            print("a, b, c= ", a, int(b), c)
        bar(a, **options)
        options = {'c': 5, 'b': 10}
        bar(a, **options)
        return None

    def check_args(args):
        deparse_test(inspect.currentframe().f_code)
        for i in range(2):
            try:
                i  = int(args[i])
            except ValueError:
                print("** Expecting an integer, got: %s" % repr(args[i]))
                sys.exit(2)
                pass
            pass

    def gcd(a, b):
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
    # deparse_test(get_code_for_fn(Traverser.fixup_offsets))
    # deparse_test(inspect.currentframe().f_code)
