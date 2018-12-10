#  Copyright (c) 2015-2018 by Rocky Bernstein
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
Creates Python source code from an uncompyle6 parse tree,
and indexes fragments which can be accessed by instruction offset
address.

See https://github.com/rocky/python-uncompyle6/wiki/Table-driven-semantic-actions.
for a more complete explanation, nicely marked up and with examples.

We add some format specifiers here not used in pysource

1. %x
-----

   %x takes an argument (src, (dest...)) and copies all of the range attributes
from src to all nodes under dest.

For example in:
    'import': ( '%|import %c%x\n', 2, (2,(0,1)), ),

node 2 range information, it in %c, is copied to nodes 0 and 1. If
1. is a nonterminal, all the nodes under it get node2 range information.

2. %r
-----

   %r associates recursively location information for the string that follows

For example in:
   'break':	( '%|%rbreak\n', ),

The node will be associated with the text break, excluding the trailing newline.

Note we associate the accumulated text with the node normally, but we just don't
do it recursively which is where offsets are probably located.

2. %b
-----

   %b associates the text from the specified index to what we have now.
      it takes an integer argument.

For example in:
  'importmultiple':   ( '%|import%b %c%c\n', 0, 2, 3 ),

The node position 0 will be associated with "import".

"""

# FIXME: DRY code with pysource

from __future__ import print_function

import re

from xdis.code import iscode
from xdis.magics import sysinfo2float
from uncompyle6.semantics import pysource
from uncompyle6 import parser
from uncompyle6.scanner import Token, Code, get_scanner
import uncompyle6.parser as python_parser
from uncompyle6.semantics.check_ast import checker
from uncompyle6 import IS_PYPY

from uncompyle6.show import (
    maybe_show_asm,
    maybe_show_tree,
)

from uncompyle6.parsers.treenode import SyntaxTree

from uncompyle6.semantics.pysource import (
    ParserError, StringIO)

from uncompyle6.semantics.consts import (
    INDENT_PER_LEVEL, NONE, PRECEDENCE,
    TABLE_DIRECT, escape, MAP, PASS
    )

from spark_parser import DEFAULT_DEBUG as PARSER_DEFAULT_DEBUG
from spark_parser.ast import GenericASTTraversalPruningException

from collections import namedtuple
NodeInfo = namedtuple("NodeInfo", "node start finish")
ExtractInfo = namedtuple("ExtractInfo",
                         "lineNo lineStartOffset markerLine selectedLine selectedText nonterminal")

TABLE_DIRECT_FRAGMENT = {
    'break':	        ( '%|%rbreak\n', ),
    'continue  ':	( '%|%rcontinue\n', ),
    'pass':	        ( '%|%rpass\n', ),
    'raise_stmt0':	( '%|%rraise\n', ),
    'import':	        ( '%|import %c%x\n', 2, (2, (0, 1)), ),
    'import_cont':  ( ', %c%x', (2, 'alias'), (2, (0, 1)), ),
    'import_from':  ( '%|from %[2]{pattr}%x import %c\n',
                        (2, (0, 1)), (3, 'importlist'), ),
    'importfrom':	( '%|from %[2]{pattr}%x import %c\n', (2, (0, 1)), 3),

    # FIXME only in <= 2.4
    'importmultiple':   ( '%|import%b %c%c\n', 0, 2, 3 ),

    'list_for':	  	(' for %c%x in %c%c', 2, (2, (1, )), 0, 3 ),
    'for':
        ('%|for%b %c%x in %c:\n%+%c%-\n\n',
         0, (3, 'store'), (3, (2,)), 1, 4 ),
    'forelsestmt':
        ('%|for%b %c%x in %c:\n%+%c%-%|else:\n%+%c%-\n\n',
         0, (3, 'store'), (3, (2,)), 1, 4, -2),
    'forelselaststmt':
        ('%|for%b %c%x in %c:\n%+%c%-%|else:\n%+%c%-',
         0, (3, 'store'), (3, (2,)), 1, 4, -2),
    'forelselaststmtl':
        ('%|for%b %c%x in %c:\n%+%c%-%|else:\n%+%c%-\n\n',
         0, (3, 'store'), (3, (2,)), 1, 4, -2),

    'whilestmt':	( '%|while%b %c:\n%+%c%-\n\n', 0, 1, 2 ),
    'whileelsestmt':	( '%|while%b %c:\n%+%c%-%|else:\n%+%c%-\n\n', 0, 1, 2, -2 ),
    'whileelselaststmt':	( '%|while%b %c:\n%+%c%-%|else:\n%+%c%-', 0, 1, 2, -2 ),
    }


class FragmentsWalker(pysource.SourceWalker, object):

    MAP_DIRECT_FRAGMENT = ()

    stacked_params = ('f', 'indent', 'is_lambda', '_globals')

    def __init__(self, version, scanner, showast=False,
                 debug_parser=PARSER_DEFAULT_DEBUG,
                 compile_mode='exec', is_pypy=False, tolerate_errors=True):
        pysource.SourceWalker.__init__(self, version=version, out=StringIO(),
                                       scanner=scanner,
                                       showast=showast, debug_parser=debug_parser,
                                       compile_mode=compile_mode, is_pypy=is_pypy,
                                       tolerate_errors=tolerate_errors)

        # hide_internal suppresses displaying the additional instructions that sometimes
        # exist in code but but were not written in the source code.
        # An example is:
        # __module__ = __name__
        # If showing source code we generally don't want to show this. However in fragment
        # deparsing we generally do need to see these instructions since we may be stopped
        # at one. So here we do not want to suppress showing such instructions.
        self.hide_internal = False
        self.offsets = {}
        self.last_finish = -1

        # FIXME: is there a better way?
        global MAP_DIRECT_FRAGMENT
        MAP_DIRECT_FRAGMENT = dict(TABLE_DIRECT, **TABLE_DIRECT_FRAGMENT),
        return

    f = property(lambda s: s.params['f'],
                 lambda s, x: s.params.__setitem__('f', x),
                 lambda s: s.params.__delitem__('f'),
                 None)

    indent = property(lambda s: s.params['indent'],
                      lambda s, x: s.params.__setitem__('indent', x),
                      lambda s: s.params.__delitem__('indent'),
                      None)

    is_lambda = property(lambda s: s.params['is_lambda'],
                         lambda s, x: s.params.__setitem__('is_lambda', x),
                         lambda s: s.params.__delitem__('is_lambda'),
                         None)

    _globals = property(lambda s: s.params['_globals'],
                        lambda s, x: s.params.__setitem__('_globals', x),
                        lambda s: s.params.__delitem__('_globals'),
                        None)

    def set_pos_info(self, node, start, finish, name=None):
        if name is None: name = self.name
        if hasattr(node, 'offset'):
            node.start = start
            node.finish = finish
            self.offsets[name, node.offset] = node

        if hasattr(node, 'parent'):
            assert node.parent != node

        node.start  = start
        node.finish = finish
        self.last_finish = finish

    def preorder(self, node=None):
        start = len(self.f.getvalue())
        super(pysource.SourceWalker, self).preorder(node)
        self.set_pos_info(node, start, len(self.f.getvalue()))

        return

    def table_r_node(self, node):
        """General pattern where the last node should should
        get the text span attributes of the entire tree"""
        start = len(self.f.getvalue())
        try:
            self.default(node)
        except GenericASTTraversalPruningException:
            final = len(self.f.getvalue())
            self.set_pos_info(node, start, final)
            self.set_pos_info(node[-1], start, final)
            raise GenericASTTraversalPruningException

    n_slice0 = n_slice1 = n_slice2 = n_slice3 = n_subscript = table_r_node
    n_aug_assign_1 = n_print_item = exec_stmt = print_to_item = del_stmt = table_r_node
    n_classdefco1 = n_classdefco2 = except_cond1 = except_cond2 = table_r_node

    def n_pass(self, node):
        start = len(self.f.getvalue()) + len(self.indent)
        self.set_pos_info(node, start, start+len("pass"))
        self.default(node)

    def n_try_except(self, node):
        # Note: we could also do this via modifying the
        # 5 or so template rules. That is change:
        #  'try_except':  ( '%|try%:\n%+%c%-%c\n\n', 1, 3 ),
        # to:
        #  'try_except':  ( '%|try%b:\n%+%c%-%c\n\n', 0, 1, 3 ),

        start = len(self.f.getvalue()) + len(self.indent)
        self.set_pos_info(node[0], start, start+len("try:"))
        self.default(node)

    n_tryelsestmt = n_tryelsestmtc = n_tryelsestmtl = n_tryfinallystmt = n_try_except

    def n_raise_stmt0(self, node):
        assert node[0] == 'RAISE_VARARGS_0'
        start = len(self.f.getvalue()) + len(self.indent)
        try:
            self.default(node)
        except GenericASTTraversalPruningException:
            self.set_pos_info(node[0], start, len(self.f.getvalue()))
            self.prune()

    def n_raise_stmt1(self, node):
        assert node[1] == 'RAISE_VARARGS_1'
        start = len(self.f.getvalue()) + len(self.indent)
        try:
            self.default(node)
        except GenericASTTraversalPruningException:
            self.set_pos_info(node[1], start, len(self.f.getvalue()))
            self.prune()

    def n_raise_stmt2(self, node):
        assert node[2] == 'RAISE_VARARGS_2'
        start = len(self.f.getvalue()) + len(self.indent)
        try:
            self.default(node)
        except GenericASTTraversalPruningException:
            self.set_pos_info(node[2], start, len(self.f.getvalue()))
            self.prune()

    # FIXME: Isolate: only in Python 2.x.
    def n_raise_stmt3(self, node):
        assert node[3] == 'RAISE_VARARGS_3'
        start = len(self.f.getvalue()) + len(self.indent)
        try:
            self.default(node)
        except GenericASTTraversalPruningException:
            self.set_pos_info(node[3], start, len(self.f.getvalue()))
            self.prune()

    def n_return(self, node):
        start = len(self.f.getvalue()) + len(self.indent)
        if self.params['is_lambda']:
            self.preorder(node[0])
            if hasattr(node[-1], 'offset'):
                self.set_pos_info(node[-1], start,
                len(self.f.getvalue()))
            self.prune()
        else:
            start = len(self.f.getvalue()) + len(self.indent)
            self.write(self.indent, 'return')
            if self.return_none or node != SyntaxTree('return', [SyntaxTree('ret_expr', [NONE]),
                                                          Token('RETURN_VALUE')]):
                self.write(' ')
                self.last_finish = len(self.f.getvalue())
                self.preorder(node[0])
                if hasattr(node[-1], 'offset'):
                    self.set_pos_info(node[-1], start, len(self.f.getvalue()))
                    pass
                pass
            else:
                for n in node:
                    self.set_pos_info_recurse(n, start, len(self.f.getvalue()))
                    pass
                pass
            self.set_pos_info(node, start, len(self.f.getvalue()))
            self.println()
            self.prune() # stop recursing

    def n_return_if_stmt(self, node):

        start = len(self.f.getvalue()) + len(self.indent)
        if self.params['is_lambda']:
            node[0].parent = node
            self.preorder(node[0])
        else:
            start = len(self.f.getvalue()) + len(self.indent)
            self.write(self.indent, 'return')
            if self.return_none or node != SyntaxTree('return', [SyntaxTree('ret_expr', [NONE]), Token('RETURN_END_IF')]):
                self.write(' ')
                self.preorder(node[0])
                if hasattr(node[-1], 'offset'):
                    self.set_pos_info(node[-1], start, len(self.f.getvalue()))
            self.println()
        self.set_pos_info(node, start, len(self.f.getvalue()))
        self.prune() # stop recursing

    def n_yield(self, node):
        start = len(self.f.getvalue())
        try:
            super(FragmentsWalker, self).n_yield(node)
        except GenericASTTraversalPruningException:
            pass
        if node != SyntaxTree('yield', [NONE, Token('YIELD_VALUE')]):
            node[0].parent = node
        self.set_pos_info(node[-1], start, len(self.f.getvalue()))
        self.set_pos_info(node, start, len(self.f.getvalue()))
        self.prune() # stop recursing

    # In Python 3.3+ only
    def n_yield_from(self, node):
        start = len(self.f.getvalue())
        try:
            super(FragmentsWalker, self).n_yield(node)
        except GenericASTTraversalPruningException:
            pass
        self.preorder(node[0])
        self.set_pos_info(node, start, len(self.f.getvalue()))
        self.prune() # stop recursing

    def n_buildslice3(self, node):
        start = len(self.f.getvalue())
        try:
            super(FragmentsWalker, self).n_buildslice3(node)
        except GenericASTTraversalPruningException:
            pass
        self.set_pos_info(node, start, len(self.f.getvalue()))
        self.prune() # stop recursing

    def n_buildslice2(self, node):
        start = len(self.f.getvalue())
        try:
            super(FragmentsWalker, self).n_buildslice2(node)
        except GenericASTTraversalPruningException:
            pass
        self.set_pos_info(node, start, len(self.f.getvalue()))
        self.prune() # stop recursing

    def n_expr(self, node):
        start = len(self.f.getvalue())
        p = self.prec
        if node[0].kind.startswith('binary_expr'):
            n = node[0][-1][0]
        else:
            n = node[0]
        self.prec = PRECEDENCE.get(n.kind, -2)
        if n == 'LOAD_CONST' and repr(n.pattr)[0] == '-':
            n.parent = node
            self.set_pos_info(n, start, len(self.f.getvalue()))
            self.prec = 6
        if p < self.prec:
            self.write('(')
            node[0].parent = node
            self.last_finish = len(self.f.getvalue())
            self.preorder(node[0])
            finish = len(self.f.getvalue())
            if hasattr(node[0], 'offset'):
                self.set_pos_info(node[0], start, len(self.f.getvalue()))
            self.write(')')
            self.last_finish = finish + 1
        else:
            node[0].parent = node
            start = len(self.f.getvalue())
            self.preorder(node[0])
            if hasattr(node[0], 'offset'):
                self.set_pos_info(node[0], start, len(self.f.getvalue()))
        self.prec = p
        self.set_pos_info(node, start, len(self.f.getvalue()))
        self.prune()

    def n_ret_expr(self, node):
        start = len(self.f.getvalue())
        super(FragmentsWalker, self).n_ret_expr(node)
        self.set_pos_info(node, start, len(self.f.getvalue()))

    def n_binary_expr(self, node):
        start = len(self.f.getvalue())
        for n in node:
            n.parent = node
        self.last_finish = len(self.f.getvalue())
        try:
            super(FragmentsWalker, self).n_binary_expr(node)
        except GenericASTTraversalPruningException:
            pass
        self.set_pos_info(node, start, len(self.f.getvalue()))
        self.prune()

    def n_LOAD_CONST(self, node):
        start = len(self.f.getvalue())
        try:
            super(FragmentsWalker, self).n_LOAD_CONST(node)
        except GenericASTTraversalPruningException:
            pass
        self.set_pos_info(node, start, len(self.f.getvalue()))
        self.prune()

    def n_exec_stmt(self, node):
        """
        exec_stmt ::= expr exprlist DUP_TOP EXEC_STMT
        exec_stmt ::= expr exprlist EXEC_STMT
        """
        start = len(self.f.getvalue()) + len(self.indent)
        try:
            super(FragmentsWalker, self).n_exec_stmt(node)
        except GenericASTTraversalPruningException:
            pass
        self.set_pos_info(node, start, len(self.f.getvalue()))
        self.set_pos_info(node[-1], start, len(self.f.getvalue()))
        self.prune() # stop recursing

    def n_ifelsestmtr(self, node):
        if node[2] == 'COME_FROM':
            return_stmts_node = node[3]
            node.kind = 'ifelsestmtr2'
        else:
            return_stmts_node = node[2]
        if len(return_stmts_node) != 2:
            self.default(node)

        if (not (return_stmts_node[0][0][0] == 'ifstmt'
                 and return_stmts_node[0][0][0][1][0] == 'return_if_stmts')
            and not (return_stmts_node[0][-1][0] == 'ifstmt'
                     and return_stmts_node[0][-1][0][1][0] == 'return_if_stmts')):
            self.default(node)
            return

        start = len(self.f.getvalue()) + len(self.indent)
        self.write(self.indent, 'if ')
        self.preorder(node[0])
        self.println(':')
        self.indent_more()
        node[1].parent = node
        self.preorder(node[1])
        self.indent_less()

        if_ret_at_end = False
        if len(node[2][0]) >= 3:
            node[2][0].parent = node
            if node[2][0][-1][0] == 'ifstmt' and node[2][0][-1][0][1][0] == 'return_if_stmts':
                if_ret_at_end = True

        past_else = False
        prev_stmt_is_if_ret = True
        for n in return_stmts_node[0]:
            if (n[0] == 'ifstmt' and n[0][1][0] == 'return_if_stmts'):
                if prev_stmt_is_if_ret:
                    n[0].kind = 'elifstmt'
                prev_stmt_is_if_ret = True
            else:
                prev_stmt_is_if_ret = False
                if not past_else and not if_ret_at_end:
                    self.println(self.indent, 'else:')
                    self.indent_more()
                    past_else = True
            n.parent = node
            self.preorder(n)
        if not past_else or if_ret_at_end:
            self.println(self.indent, 'else:')
            self.indent_more()
        node[2][1].parent = node
        self.preorder(node[2][1])
        self.set_pos_info(node, start, len(self.f.getvalue()))
        self.indent_less()
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
        self.indent_more()
        node[1].parent = node
        self.preorder(node[1])
        self.indent_less()

        for n in node[2][0]:
            n[0].kind = 'elifstmt'
            n.parent = node
            self.preorder(n)
        self.println(self.indent, 'else:')
        self.indent_more()
        node[2][1].parent = node
        self.preorder(node[2][1])
        self.indent_less()
        self.set_pos_info(node, start, len(self.f.getvalue()))
        self.prune()

    def n_alias(self, node):
        start = len(self.f.getvalue())
        iname = node[0].pattr

        store_import_node = node[-1][-1]
        assert store_import_node.kind.startswith('STORE_')

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

        if self.version >= 3.3 or node[-2] == 'kwargs':
            # LOAD_CONST code object ..
            # LOAD_CONST        'x0'  if >= 3.3
            # MAKE_FUNCTION ..
            code_node = node[-3]
        elif node[-2] == 'expr':
            code_node = node[-2][0]
        else:
            # LOAD_CONST code object ..
            # MAKE_FUNCTION ..
            code_node = node[-2]
        func_name = code_node.attr.co_name
        self.write(func_name)
        self.set_pos_info(code_node, start, len(self.f.getvalue()))

        self.indent_more()
        start = len(self.f.getvalue())
        self.make_function(node, is_lambda=False, code_node=code_node)

        self.set_pos_info(node, start, len(self.f.getvalue()))

        if len(self.param_stack) > 1:
            self.write('\n\n')
        else:
            self.write('\n\n\n')
        self.indent_less()
        self.prune() # stop recursing

    def n_list_comp(self, node):
        """List comprehensions"""
        p = self.prec
        self.prec = 27
        n = node[-1]
        assert n == 'list_iter'
        # find innermost node
        while n == 'list_iter':
            n = n[0] # recurse one step
            if   n == 'list_for':	n = n[3]
            elif n == 'list_if':	n = n[2]
            elif n == 'list_if_not': n= n[2]
        assert n == 'lc_body'
        if node[0].kind.startswith('BUILD_LIST'):
            start = len(self.f.getvalue())
            self.set_pos_info(node[0], start, start+1)
        self.write( '[ ')
        self.preorder(n[0]) # lc_body
        self.preorder(node[-1]) # for/if parts
        self.write( ' ]')
        self.prec = p
        self.prune() # stop recursing

    def comprehension_walk(self, node, iter_index, code_index=-5):
        p = self.prec
        self.prec = 27

        # FIXME: clean this up
        if self.version > 3.0 and node == 'dict_comp':
            cn = node[1]
        elif self.version > 3.0 and node == 'generator_exp':
            if node[0] == 'load_genexpr':
                load_genexpr = node[0]
            elif node[1] == 'load_genexpr':
                load_genexpr = node[1]
            cn = load_genexpr[0]
        elif hasattr(node[code_index], 'attr'):
            # Python 2.5+ (and earlier?) does this
            cn = node[code_index]
        else:
            if len(node[1]) > 1 and hasattr(node[1][1], 'attr'):
                # Python 3.3+ does this
                cn = node[1][1]
            elif hasattr(node[1][0], 'attr'):
                # Python 3.2 does this
                cn = node[1][0]
            else:
                assert False, "Can't find code for comprehension"

        assert iscode(cn.attr)

        code = Code(cn.attr, self.scanner, self.currentclass)
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
        store = ast[iter_index-1]
        self.preorder(store)
        self.set_pos_info(ast[iter_index-1], start, len(self.f.getvalue()))
        self.write(' in ')
        start = len(self.f.getvalue())
        node[-3].parent = node
        self.preorder(node[-3])
        self.set_pos_info(node[-3], start, len(self.f.getvalue()))
        start = len(self.f.getvalue())
        self.preorder(ast[iter_index])
        self.set_pos_info(ast[iter_index], start, len(self.f.getvalue()))
        self.prec = p

    def comprehension_walk3(self, node, iter_index, code_index=-5):
        """
        List comprehensions the way they are done in Python3.
        They're more other comprehensions, e.g. set comprehensions
        See if we can combine code.
        """
        p = self.prec
        self.prec = 27
        code = node[code_index].attr

        assert iscode(code), node[code_index]
        code_name = code.co_name
        code = Code(code, self.scanner, self.currentclass)

        ast = self.build_ast(code._tokens, code._customize)

        self.customize(code._customize)
        if ast[0] == 'sstmt':
            ast = ast[0]

        # skip over stmt return ret_expr
        ast = ast[0][0][0]
        store = None
        if ast in ['set_comp_func', 'dict_comp_func']:
            # Offset 0: BUILD_SET should have the span
            # of '{'
            self.gen_source(ast, code_name, {})
            for k in ast:
                if k == 'comp_iter':
                    n = k
                elif k == 'store':
                    store = k
                    pass
                pass
            pass
        else:
            ast = ast[0][0]
            n = ast[iter_index]
            assert n == 'list_iter', n

        # FIXME: I'm not totally sure this is right.

        # Find the list comprehension body. It is the inner-most
        # node that is not list_.. .
        if_node = None
        comp_for = None
        comp_store = None
        if n == 'comp_iter':
            comp_for = n
            comp_store = ast[3]

        have_not = False
        while n in ('list_iter', 'comp_iter'):
            n = n[0] # iterate one nesting deeper
            if n in ('list_for', 'comp_for'):
                if n[2] == 'store':
                    store = n[2]
                n = n[3]
            elif n in ('list_if', 'list_if_not', 'comp_if', 'comp_ifnot'):
                have_not = n in ('list_if_not', 'comp_ifnot')
                if_node = n[0]
                if n[1] == 'store':
                    store = n[1]
                n = n[2]
                pass
            pass

        # Python 2.7+ starts including set_comp_body
        # Python 3.5+ starts including set_comp_func
        assert n.kind in ('lc_body', 'comp_body', 'set_comp_func', 'set_comp_body'), ast
        assert store, "Couldn't find store in list/set comprehension"

        old_name = self.name
        self.name = code_name

        # Issue created with later Python code generation is that there
        # is a lamda set up with a dummy argument name that is then called
        # So we can't just translate that as is but need to replace the
        # dummy name. Below we are picking out the variable name as seen
        # in the code. And trying to generate code for the other parts
        # that don't have the dummy argument name in it.
        # Another approach might be to be able to pass in the source name
        # for the dummy argument.

        self.preorder(n[0])
        gen_start = len(self.f.getvalue()) + 1
        self.write(' for ')
        start = len(self.f.getvalue())
        if comp_store:
            self.preorder(comp_store)
        else:
            self.preorder(store)

        self.set_pos_info(store, start, len(self.f.getvalue()))

        # FIXME this is all merely approximate
        # from trepan.api import debug; debug()
        self.write(' in ')
        start = len(self.f.getvalue())
        node[-3].parent = node
        self.preorder(node[-3])
        fin = len(self.f.getvalue())
        self.set_pos_info(node[-3], start, fin, old_name)

        if ast == 'list_comp':
            list_iter = ast[1]
            assert list_iter == 'list_iter'
            if list_iter == 'list_for':
                self.preorder(list_iter[3])
                self.prec = p
                return
            pass

        if comp_store:
            self.preorder(comp_for)
        elif if_node:
            self.write(' if ')
            if have_not:
                self.write('not ')
            self.preorder(if_node)
            pass
        self.prec = p
        self.name = old_name
        if node[-1].kind.startswith('CALL_FUNCTION'):
            self.set_pos_info(node[-1], gen_start, len(self.f.getvalue()))

    def listcomprehension_walk2(self, node):
        """List comprehensions the way they are done in Python 2 (and
        some Python 3?).
        They're more other comprehensions, e.g. set comprehensions
        See if we can combine code.
        """
        p = self.prec
        self.prec = 27

        code = Code(node[1].attr, self.scanner, self.currentclass)
        ast = self.build_ast(code._tokens, code._customize)
        self.customize(code._customize)
        if node == 'set_comp':
            ast = ast[0][0][0]
        else:
            ast = ast[0][0][0][0][0]

        if ast == 'expr':
            ast = ast[0]

        n = ast[1]
        collection = node[-3]
        list_if = None
        assert n == 'list_iter'

        # Find the list comprehension body. It is the inner-most
        # node that is not list_.. .
        while n == 'list_iter':
            n = n[0] # recurse one step
            if n == 'list_for':
                store = n[2]
                n = n[3]
            elif n in ('list_if', 'list_if_not'):
                # FIXME: just a guess
                if n[0].kind == 'expr':
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
        self.preorder(store)
        self.set_pos_info(store, start, len(self.f.getvalue()))
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

    def n_generator_exp(self, node):
        start = len(self.f.getvalue())
        self.write('(')
        code_index = -6 if self.version > 3.2 else -5
        self.comprehension_walk(node, iter_index=3, code_index=code_index)
        self.write(')')
        self.set_pos_info(node, start, len(self.f.getvalue()))
        self.prune()

    def n_set_comp(self, node):
        start = len(self.f.getvalue())
        self.write('{')
        if node[0] in ['LOAD_SETCOMP', 'LOAD_DICTCOMP']:
            start = len(self.f.getvalue())
            self.set_pos_info(node[0], start-1, start)
            self.comprehension_walk3(node, 1, 0)
        elif node[0].kind == 'load_closure':
            self.setcomprehension_walk3(node, collection_index=4)
        else:
            self.comprehension_walk(node, iter_index=4)
        self.write('}')
        self.set_pos_info(node, start, len(self.f.getvalue()))
        self.prune()

    # FIXME: Not sure if below is general. Also, add dict_comp_func.
    # 'set_comp_func': ("%|lambda %c: {%c for %c in %c%c}\n", 1, 3, 3, 1, 4)
    def n_set_comp_func(self, node):
        setcomp_start = len(self.f.getvalue())
        self.write(self.indent, "lambda ")
        param_node = node[1]
        start = len(self.f.getvalue())
        self.preorder(param_node)
        self.set_pos_info(node[0], start, len(self.f.getvalue()))
        self.write(': {')
        start = len(self.f.getvalue())
        assert node[0].kind.startswith('BUILD_SET')
        self.set_pos_info(node[0], start-1, start)
        store = node[3]
        assert store == 'store'
        start = len(self.f.getvalue())
        self.preorder(store)
        fin = len(self.f.getvalue())
        self.set_pos_info(store, start, fin)
        for_iter_node = node[2]
        assert for_iter_node.kind == 'FOR_ITER'
        self.set_pos_info(for_iter_node, start, fin)
        self.write(" for ")
        self.preorder(store)
        self.write(" in ")
        self.preorder(param_node)
        start = len(self.f.getvalue())
        self.preorder(node[4])
        self.set_pos_info(node[4], start, len(self.f.getvalue()))
        self.write("}")
        fin = len(self.f.getvalue())
        self.set_pos_info(node, setcomp_start, fin)
        if node[-2] == 'RETURN_VALUE':
            self.set_pos_info(node[-2], setcomp_start, fin)

        self.prune()

    def n_listcomp(self, node):
        self.write('[')
        if node[0].kind == 'load_closure':
            self.listcomprehension_walk2(node)
        else:
            if node[0] == 'LOAD_LISTCOMP':
                start = len(self.f.getvalue())
                self.set_pos_info(node[0], start-1, start)
            self.comprehension_walk3(node, 1, 0)
        self.write(']')
        self.prune()

    def n__ifstmts_jump_exit(self, node):
        if len(node) > 1:
            if (node[0] == 'c_stmts_opt' and
                node[0][0] == 'pass' and
                node[1].kind.startswith('JUMP_FORWARD')):
                self.set_pos_info(node[1], node[0][0].start, node[0][0].finish)

    def setcomprehension_walk3(self, node, collection_index):
        """List comprehensions the way they are done in Python3.
        They're more other comprehensions, e.g. set comprehensions
        See if we can combine code.
        """
        p = self.prec
        self.prec = 27

        code = Code(node[1].attr, self.scanner, self.currentclass)
        ast = self.build_ast(code._tokens, code._customize)
        self.customize(code._customize)
        ast = ast[0][0][0]
        store = ast[3]
        collection = node[collection_index]

        n = ast[4]
        list_if = None
        assert n == 'comp_iter'

        # find innermost node
        while n == 'comp_iter':
            n = n[0] # recurse one step
            # FIXME: adjust for set comprehension
            if n == 'list_for':
                store = n[2]
                n = n[3]
            elif n in ('list_if', 'list_if_not', 'comp_if', 'comp_if_not'):
                # FIXME: just a guess
                if n[0].kind == 'expr':
                    list_if = n
                else:
                    list_if = n[1]
                n = n[2]
                pass
            pass

        assert n == 'comp_body', ast

        self.preorder(n[0])
        self.write(' for ')
        start = len(self.f.getvalue())
        self.preorder(store)
        self.set_pos_info(store, start, len(self.f.getvalue()))
        self.write(' in ')
        start = len(self.f.getvalue())
        self.preorder(collection)
        self.set_pos_info(collection, start, len(self.f.getvalue()))
        if list_if:
            start = len(self.f.getvalue())
            self.preorder(list_if)
            self.set_pos_info(list_if, start, len(self.f.getvalue()))
        self.prec = p

    def n_classdef(self, node):
        # class definition ('class X(A,B,C):')
        cclass = self.currentclass

        if self.version > 3.0:
            if node == 'classdefdeco2':
                currentclass = node[1][2].pattr
                buildclass = node
            else:
                currentclass = node[1][0].pattr
                buildclass = node[0]

            if buildclass[0] == 'LOAD_BUILD_CLASS':
                start = len(self.f.getvalue())
                self.set_pos_info(buildclass[0], start, start + len('class')+2)

            assert 'mkfunc' == buildclass[1]
            mkfunc = buildclass[1]
            if mkfunc[0] == 'kwargs':
                for n in mkfunc:
                    if hasattr(n, 'attr') and iscode(n.attr):
                        subclass = n.attr
                        break
                    pass
                subclass_info = node if node == 'classdefdeco2' else node[0]
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
            buildclass = node if (node == 'classdefdeco2') else node[0]
            build_list = buildclass[1][0]
            if hasattr(buildclass[-3][0], 'attr'):
                subclass = buildclass[-3][0].attr
                currentclass = buildclass[0].pattr
            elif hasattr(node[0][0], 'pattr'):
                subclass = buildclass[-3][1].attr
                currentclass = node[0][0].pattr
            else:
                raise 'Internal Error n_classdef: cannot find class name'

        if (node == 'classdefdeco2'):
            self.write('\n')
        else:
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
        self.indent_more()
        self.build_class(subclass)
        self.indent_less()

        self.currentclass = cclass
        self.set_pos_info(node, start, len(self.f.getvalue()))
        if len(self.param_stack) > 1:
            self.write('\n\n')
        else:
            self.write('\n\n\n')

        self.prune()

    n_classdefdeco2 = n_classdef

    def gen_source(self, ast, name, customize, is_lambda=False, returnNone=False):
        """convert parse tree to Python source code"""

        rn = self.return_none
        self.return_none = returnNone
        old_name = self.name
        self.name = name
        # if code would be empty, append 'pass'
        if len(ast) == 0:
            self.println(self.indent, 'pass')
        else:
            self.customize(customize)
            self.text = self.traverse(ast, is_lambda=is_lambda)
        self.name = old_name
        self.return_none = rn

    def build_ast(self, tokens, customize, is_lambda=False,
                  noneInNames=False, isTopLevel=False):

        # FIXME: DRY with pysource.py

        # assert isinstance(tokens[0], Token)

        if is_lambda:
            for t in tokens:
                if t.kind == 'RETURN_END_IF':
                    t.kind = 'RETURN_END_IF_LAMBDA'
                elif t.kind == 'RETURN_VALUE':
                    t.kind = 'RETURN_VALUE_LAMBDA'
            tokens.append(Token('LAMBDA_MARKER'))
            try:
                # FIXME: have p.insts update in a better way
                # modularity is broken here
                p_insts = self.p.insts
                self.p.insts = self.scanner.insts
                ast = python_parser.parse(self.p, tokens, customize)
                self.p.insts = p_insts
            except (parser.ParserError, AssertionError) as e:
                raise ParserError(e, tokens)
            maybe_show_tree(self, ast)
            return ast

        # The bytecode for the end of the main routine has a
        # "return None". However you can't issue a "return" statement in
        # main. In the other build_ast routine we eliminate the
        # return statement instructions before parsing.
        # But here we want to keep these instructions at the expense of
        # a fully runnable Python program because we
        # my be queried about the role of one of those instructions.
        #
        # NOTE: this differs from behavior in pysource.py

        if self.hide_internal:
            if len(tokens) >= 2 and not noneInNames:
                if tokens[-1].kind in ('RETURN_VALUE', 'RETURN_VALUE_LAMBDA'):
                    # Python 3.4's classes can add a "return None" which is
                    # invalid syntax.
                    if tokens[-2].kind == 'LOAD_CONST':
                        if isTopLevel or tokens[-2].pattr is None:
                            del tokens[-2:]
                        else:
                            tokens.append(Token('RETURN_LAST'))
                    else:
                        tokens.append(Token('RETURN_LAST'))
            if len(tokens) == 0:
                return PASS

        # Build parse tree from tokenized and massaged disassembly.
        try:
            # FIXME: have p.insts update in a better way
            # modularity is broken here
            p_insts = self.p.insts
            self.p.insts = self.scanner.insts
            ast = parser.parse(self.p, tokens, customize)
            self.p.insts = p_insts
        except (parser.ParserError, AssertionError) as e:
            raise ParserError(e, tokens)

        maybe_show_tree(self, ast)

        checker(ast, False, self.ast_errors)

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

    def set_pos_info_recurse(self, node, start, finish, parent=None):
        """Set positions under node"""
        self.set_pos_info(node, start, finish)
        if parent is None:
            parent = node
        for n in node:
            n.parent = parent
            if hasattr(n, 'offset'):
                self.set_pos_info(n, start, finish)
            else:
                n.start = start
                n.finish = finish
                self.set_pos_info_recurse(n, start, finish, parent)
        return

    def node_append(self, before_str, node_text, node):
        self.write(before_str)
        self.last_finish = len(self.f.getvalue())
        self.fixup_offsets(self.last_finish, node)
        self.write(node_text)
        self.last_finish = len(self.f.getvalue())

    # FIXME: duplicated from pysource, since we don't find self.params
    def traverse(self, node, indent=None, is_lambda=False):
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
            'is_lambda': is_lambda,
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

        if isinstance(nodeInfo, Token):
            nodeInfo = nodeInfo.parent
        else:
            nodeInfo = nodeInfo

        if isinstance(nodeInfo, SyntaxTree):
            nonterminal = nodeInfo[0]
        else:
            nonterminal = nodeInfo.node

        return ExtractInfo(lineNo = len(lines), lineStartOffset = lineStart,
                           markerLine = markerLine,
                           selectedLine = selectedLine,
                           selectedText = selectedText,
                           nonterminal = nonterminal)

    def extract_line_info(self, name, offset):
        if (name, offset) not in list(self.offsets.keys()):
            return None
        return self.extract_node_info(self.offsets[name, offset])

    def prev_node(self, node):
        prev = None
        if not hasattr(node, 'parent'):
            return prev
        p = node.parent
        for n in p:
            if node == n:
                return prev
            prev = n
        return prev

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
        assert node[n].kind.startswith('CALL_FUNCTION')

        for i in range(n-2, 0, -1):
            if not node[i].kind in ['expr', 'LOAD_CLASSNAME']:
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

    def n_dict(self, node):
        """
        prettyprint a dict
        'dict' is something like k = {'a': 1, 'b': 42 }"
        """
        p = self.prec
        self.prec = 100

        self.indent_more(INDENT_PER_LEVEL)
        line_seperator = ',\n' + self.indent
        sep = INDENT_PER_LEVEL[:-1]
        start = len(self.f.getvalue())
        self.write('{')
        self.set_pos_info(node[0], start, start+1)

        if self.version >= 3.0 and not self.is_pypy:
            if node[0].kind.startswith('kvlist'):
                # Python 3.5+ style key/value list in dict
                kv_node = node[0]
                l = list(kv_node)
                length = len(l)
                if kv_node[-1].kind.startswith("BUILD_MAP"):
                    length -= 1
                i = 0
                while i < length:
                    self.write(sep)
                    name = self.traverse(l[i], indent='')
                    l[i].parent = kv_node
                    l[i+1].parent = kv_node
                    self.write(name, ': ')
                    value = self.traverse(l[i+1], indent=self.indent+(len(name)+2)*' ')
                    self.write(sep, name, ': ', value)
                    sep = line_seperator
                    i += 2
                    pass
                pass
            elif node[1].kind.startswith('kvlist'):
                # Python 3.0..3.4 style key/value list in dict
                kv_node = node[1]
                l = list(kv_node)
                if len(l) > 0 and l[0].kind == 'kv3':
                    # Python 3.2 does this
                    kv_node = node[1][0]
                    l = list(kv_node)
                i = 0
                while i < len(l):
                    l[i].parent = kv_node
                    l[i+1].parent = kv_node
                    key_start = len(self.f.getvalue()) + len(sep)
                    name = self.traverse(l[i+1], indent='')
                    key_finish = key_start + len(name)
                    val_start = key_finish + 2
                    value = self.traverse(l[i], indent=self.indent+(len(name)+2)*' ')
                    self.write(sep, name, ': ', value)
                    self.set_pos_info_recurse(l[i+1], key_start, key_finish)
                    self.set_pos_info_recurse(l[i], val_start, val_start + len(value))
                    sep = line_seperator
                    i += 3
                    pass
                pass
            pass
        else:
            # Python 2 style kvlist
            assert node[-1].kind.startswith('kvlist')
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
        self.set_pos_info(node, start, finish)
        self.indent_less(INDENT_PER_LEVEL)
        self.prec = p
        self.prune()

    def n_list(self, node):
        """
        prettyprint a list or tuple
        """
        p = self.prec
        self.prec = 100
        n = node.pop()
        lastnode = n.kind
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
            raise RuntimeError('Internal Error: n_list expects list or tuple')

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

        self.indent_more(INDENT_PER_LEVEL)
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
        self.indent_less(INDENT_PER_LEVEL)
        self.prec = p
        self.prune()
        return

    n_set = n_tuple = n_build_set = n_list

    def template_engine(self, entry, startnode):
        """The format template interpetation engine.  See the comment at the
        beginning of this module for the how we interpret format
        specifications such as %c, %C, and so on.
        """

        # print("-----")
        # print(startnode)
        # print(entry[0])
        # print('======')

        startnode_start = len(self.f.getvalue())
        start = startnode_start

        fmt = entry[0]
        arg = 1
        i = 0
        lastC = -1
        recurse_node = False

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

            elif typ == '+': self.indent_more()
            elif typ == '-': self.indent_less()
            elif typ == '|': self.write(self.indent)
            # no longer used, since BUILD_TUPLE_n is pretty printed:
            elif typ == 'r': recurse_node = True
            elif typ == ',':
                if lastC == 1:
                    self.write(',')
            elif typ == 'b':
                finish = len(self.f.getvalue())
                self.set_pos_info(node[entry[arg]], start, finish)
                arg += 1
            elif typ == 'c':
                start = len(self.f.getvalue())

                index = entry[arg]
                if isinstance(index, tuple):
                    assert node[index[0]] == index[1], (
                        "at %s[%d], expected %s node; got %s" % (
                            node.kind, arg, node[index[0]].kind, index[1])
                        )
                    index = index[0]
                assert isinstance(index, int), (
                    "at %s[%d], %s should be int or tuple" % (
                        node.kind, arg, type(index)))
                self.preorder(node[index])

                finish = len(self.f.getvalue())
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
            elif typ == 'D':
                low, high, sep = entry[arg]
                lastC = remaining = len(node[low:high])
                for subnode in node[low:high]:
                    remaining -= 1
                    if len(subnode) > 0:
                        self.preorder(subnode)
                        if remaining > 0:
                            self.write(sep)
                            pass
                        pass
                    pass
                arg += 1
            elif typ == 'x':
                src, dest = entry[arg]
                for d in dest:
                    self.set_pos_info_recurse(node[d], node[src].start, node[src].finish)
                    pass
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

                # Line mapping stuff
                if (hasattr(node, 'linestart') and node.linestart
                    and hasattr(node, 'current_line_number')):
                    self.source_linemap[self.current_line_number] = node.linestart
                # Additional fragment-position stuff
                try:
                    start = len(self.f.getvalue())
                    self.write(eval(expr, d, d))
                    self.set_pos_info(node, start, len(self.f.getvalue()))
                except:
                    print(node)
                    raise
            m = escape.search(fmt, i)
            pass

        self.write(fmt[i:])
        fin = len(self.f.getvalue())
        if recurse_node:
            self.set_pos_info_recurse(startnode, startnode_start, fin)
        else:
            self.set_pos_info(startnode, startnode_start, fin)

        # FIXME rocky: figure out how to get these casess to be table driven.
        # 2. subroutine calls. It the last op is the call and for purposes of printing
        # we don't need to print anything special there. However it encompases the
        # entire string of the node fn(...)
        if startnode.kind == 'call':
            last_node = startnode[-1]
            self.set_pos_info(last_node, startnode_start, self.last_finish)
        return

    @classmethod
    def _get_mapping(cls, node):
        return MAP.get(node, MAP_DIRECT_FRAGMENT)

    pass

#
DEFAULT_DEBUG_OPTS = {
    'asm': False,
    'tree': False,
    'grammar': False
}

# This interface is deprecated
def deparse_code(version, co, out=StringIO(), showasm=False, showast=False,
                 showgrammar=False, code_objects={}, compile_mode='exec',
                 is_pypy=None, walker=FragmentsWalker):
    debug_opts = {
        'asm': showasm,
        'ast': showast,
        'grammar': showgrammar
    }
    return code_deparse(co, out,
                        version=version,
                        debug_opts=debug_opts,
                        code_objects=code_objects,
                        compile_mode=compile_mode,
                        is_pypy=is_pypy, walker=walker)

def code_deparse(co, out=StringIO(), version=None, is_pypy=None,
                 debug_opts=DEFAULT_DEBUG_OPTS,
                 code_objects={}, compile_mode='exec',
                 walker=FragmentsWalker):
    """
    Convert the code object co into a python source fragment.

    :param version:         The python version this code is from as a float, for
                            example 2.6, 2.7, 3.2, 3.3, 3.4, 3.5 etc.
    :param co:              The code object to parse.
    :param out:             File like object to write the output to.
    :param debug_opts:      A dictionary with keys
       'asm':     value determines whether to show
                  mangled bytecode disdassembly
       'ast':     value determines whether to show
       'grammar': boolean determining whether to show
                  grammar reduction rules.
       If value is a file-like object, output that object's write method will
       be used rather than sys.stdout

    :return: The deparsed source fragment.
    """

    assert iscode(co)

    if version is None:
        version = sysinfo2float()
    if is_pypy is None:
        is_pypy = IS_PYPY

    scanner = get_scanner(version, is_pypy=is_pypy)

    show_asm = debug_opts.get('asm', None)
    tokens, customize = scanner.ingest(co, code_objects=code_objects,
                                       show_asm=show_asm)

    tokens, customize = scanner.ingest(co)
    maybe_show_asm(show_asm, tokens)

    debug_parser = dict(PARSER_DEFAULT_DEBUG)
    show_grammar = debug_opts.get('grammar', None)
    if show_grammar:
        debug_parser['reduce'] = show_grammar
        debug_parser['errorstack'] = True

    # Build Syntax Tree from tokenized and massaged disassembly.
    # deparsed = pysource.FragmentsWalker(out, scanner, showast=showast)
    show_ast = debug_opts.get('ast', None)
    deparsed = walker(version, scanner, showast=show_ast,
                      debug_parser=debug_parser, compile_mode=compile_mode,
                      is_pypy=is_pypy)

    deparsed.ast = deparsed.build_ast(tokens, customize)

    assert deparsed.ast == 'stmts', 'Should have parsed grammar start'

    del tokens # save memory

    # convert leading '__doc__ = "..." into doc string
    assert deparsed.ast == 'stmts'
    (deparsed.mod_globs,
     nonlocals) = (pysource
                   .find_globals_and_nonlocals(deparsed.ast,
                                               set(), set(),
                                               co, version))

    # Just when you think we've forgotten about what we
    # were supposed to to: Generate source from the Syntax ree!
    deparsed.gen_source(deparsed.ast, co.co_name, customize)

    deparsed.set_pos_info(deparsed.ast, 0, len(deparsed.text))
    deparsed.fixup_parents(deparsed.ast, None)

    for g in sorted(deparsed.mod_globs):
        deparsed.write('# global %s ## Warning: Unused global\n' % g)

    if deparsed.ast_errors:
        deparsed.write("# NOTE: have decompilation errors.\n")
        deparsed.write("# Use -t option to show full context.")
        for err in deparsed.ast_errors:
            deparsed.write(err)
        deparsed.ERROR = True

    if deparsed.ERROR:
        raise deparsed.ERROR

    # To keep the API consistent with previous releases, convert
    # deparse.offset values into NodeInfo items
    for tup, node in deparsed.offsets.items():
        deparsed.offsets[tup] = NodeInfo(node = node, start = node.start,
                                         finish = node.finish)

    deparsed.scanner = scanner
    return deparsed

from bisect import bisect_right
def find_gt(a, x):
    'Find leftmost value greater than x'
    i = bisect_right(a, x)
    if i != len(a):
        return a[i]
    raise ValueError

def code_deparse_around_offset(name, offset, co, out=StringIO(),
                               version=None, is_pypy=None,
                               debug_opts=DEFAULT_DEBUG_OPTS):
    """
    Like deparse_code(), but given  a function/module name and
    offset, finds the node closest to offset. If offset is not an instruction boundary,
    we raise an IndexError.
    """
    assert iscode(co)

    if version is None:
        version = sysinfo2float()
    if is_pypy is None:
        is_pypy = IS_PYPY

    deparsed = code_deparse(co, out, version, is_pypy, debug_opts)
    if (name, offset) in deparsed.offsets.keys():
        # This is the easy case
        return deparsed

    valid_offsets = [t for t in deparsed.offsets if isinstance(t[1], int)]
    offset_list = sorted([t[1] for t in valid_offsets if t[0] == name])

    # FIXME: should check for branching?
    found_offset = find_gt(offset_list, offset)
    deparsed.offsets[name, offset] = deparsed.offsets[name, found_offset]
    return deparsed

# Deprecated. Here still for compatability
def deparse_code_around_offset(name, offset, version, co, out=StringIO(),
                               showasm=False, showast=False,
                               showgrammar=False, is_pypy=False):
    debug_opts = {
        'asm': showasm,
        'ast': showast,
        'grammar': showgrammar
    }
    return code_deparse(name, offset, co, out, version, is_pypy,
                        debug_opts)

def op_at_code_loc(code, loc, opc):
    """Return the instruction name at code[loc] using
    opc to look up instruction names. Returns 'got IndexError'
    if code[loc] is invalid.

    `code` is instruction bytecode, `loc` is an offset (integer) and
    `opc` is an opcode module from `xdis`.
    """
    try:
        op = code[loc]
    except IndexError:
        return 'got IndexError'
    return opc.opname[op]

def deparsed_find(tup, deparsed, code):
    """Return a NodeInfo nametuple for a fragment-deparsed `deparsed` at `tup`.

    `tup` is a name and offset tuple, `deparsed` is a fragment object
    and `code` is instruction bytecode.
"""
    nodeInfo = None
    name, last_i = tup
    if (name, last_i) in deparsed.offsets.keys():
        nodeInfo =  deparsed.offsets[name, last_i]
    else:
        from uncompyle6.scanner import get_scanner
        scanner = get_scanner(deparsed.version)
        co = code.co_code
        if op_at_code_loc(co, last_i, scanner.opc) == 'DUP_TOP':
            offset = deparsed.scanner.next_offset(co[last_i], last_i)
            if (name, offset) in deparsed.offsets:
                nodeInfo =  deparsed.offsets[name, offset]

    return nodeInfo

# if __name__ == '__main__':

#     def deparse_test(co, is_pypy=IS_PYPY):
#         deparsed = code_deparse(co, is_pypy=IS_PYPY)
#         print("deparsed source")
#         print(deparsed.text, "\n")
#         print('------------------------')
#         for name, offset in sorted(deparsed.offsets.keys(),
#                                    key=lambda x: str(x[0])):
#             print("name %s, offset %s" % (name, offset))
#             nodeInfo = deparsed.offsets[name, offset]
#             nodeInfo2 = deparsed_find((name, offset), deparsed, co)
#             assert nodeInfo == nodeInfo2
#             node = nodeInfo.node
#             extractInfo = deparsed.extract_node_info(node)
#             print("code: %s" % node.kind)
#             # print extractInfo
#             print(extractInfo.selectedText)
#             print(extractInfo.selectedLine)
#             print(extractInfo.markerLine)
#             extractInfo, p = deparsed.extract_parent_info(node)

#             if extractInfo:
#                 print("Contained in...")
#                 print(extractInfo.selectedLine)
#                 print(extractInfo.markerLine)
#                 print("code: %s" % p.kind)
#                 print('=' * 40)
#                 pass
#             pass
#         return

#     def deparse_test_around(offset, name, co, is_pypy=IS_PYPY):
#         deparsed = code_deparse_around_offset(name, offset, co)
#         print("deparsed source")
#         print(deparsed.text, "\n")
#         print('------------------------')
#         for name, offset in sorted(deparsed.offsets.keys(),
#                                    key=lambda x: str(x[0])):
#             print("name %s, offset %s" % (name, offset))
#             nodeInfo = deparsed.offsets[name, offset]
#             node = nodeInfo.node
#             extractInfo = deparsed.extract_node_info(node)
#             print("code: %s" % node.kind)
#             # print extractInfo
#             print(extractInfo.selectedText)
#             print(extractInfo.selectedLine)
#             print(extractInfo.markerLine)
#             extractInfo, p = deparsed.extract_parent_info(node)
#             if extractInfo:
#                 print("Contained in...")
#                 print(extractInfo.selectedLine)
#                 print(extractInfo.markerLine)
#                 print("code: %s" % p.kind)
#                 print('=' * 40)
#                 pass
#             pass
#         return

#     def get_code_for_fn(fn):
#         return fn.__code__

#     def test():
#         import os, sys

#     def div_test(a, b, c):
#         return a / b / c

#     def gcd(a, b):
#         if a > b:
#             (a, b) = (b, a)
#             pass

#         if a <= 0:
#             return None
#         if a == 1 or a == b:
#             return a
#         return gcd(b-a, a)

#     # check_args(['3', '5'])
#     # deparse_test(get_code_for_fn(gcd))
#     deparse_test(get_code_for_fn(div_test))
#     # deparse_test(get_code_for_fn(test))
#     # deparse_test(get_code_for_fn(FragmentsWalker.fixup_offsets))
#     # deparse_test(get_code_for_fn(FragmentsWalker.n_list))
#     print('=' * 30)
#     # deparse_test_around(408, 'n_list', get_code_for_fn(FragmentsWalker.n_build_list))
#     # deparse_test(inspect.currentframe().f_code)
