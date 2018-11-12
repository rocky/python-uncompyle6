#  Copyright (c) 2015-2018 by Rocky Bernstein
#  Copyright (c) 2005 by Dan Pascu <dan@windowmaker.org>
#  Copyright (c) 2000-2002 by hartmut Goebel <h.goebel@crazy-compilers.com>
#  Copyright (c) 1999 John Aycock
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

"""Creates Python source code from an uncompyle6 parse tree.

The terminal symbols are CPython bytecode instructions. (See the
python documentation under module "dis" for a list of instructions
and what they mean).

Upper levels of the grammar is a more-or-less conventional grammar for
Python.
"""

# The below is a bit long, but still it is somehwat abbreviated.
# See https://github.com/rocky/python-uncompyle6/wiki/Table-driven-semantic-actions.
# for a more complete explanation, nicely marked up and with examples.
#
#
# Semantic action rules for nonterminal symbols can be specified here by
# creating a method prefaced with "n_" for that nonterminal. For
# example, "n_exec_stmt" handles the semantic actions for the
# "exec_stmt" nonterminal symbol. Similarly if a method with the name
# of the nonterminal is suffixed with "_exit" it will be called after
# all of its children are called.
#
# After a while writing methods this way, you'll find many routines which do similar
# sorts of things, and soon you'll find you want a short notation to
# describe rules and not have to create methods at all.
#
# So another other way to specify a semantic rule for a nonterminal is via
# one of the tables MAP_R0, MAP_R, or MAP_DIRECT where the key is the
# nonterminal name.
#
# These dictionaries use a printf-like syntax to direct substitution
# from attributes of the nonterminal and its children..
#
# The rest of the below describes how table-driven semantic actions work
# and gives a list of the format specifiers. The default() and
# template_engine() methods implement most of the below.
#
# We allow for a couple of ways to interact with a node in a tree.  So
# step 1 after not seeing a custom method for a nonterminal is to
# determine from what point of view tree-wise the rule is applied.

# In the diagram below, N is a nonterminal name, and K also a nonterminal
# name but the one used as a key in the table.
# we show where those are with respect to each other in the
# parse tree for N.
#
#
#          N&K               N                  N
#         / | ... \        / | ... \          / | ... \
#        O  O      O      O  O      K         O O      O
#                                                      |
#                                                      K
#      TABLE_DIRECT      TABLE_R             TABLE_R0
#
#   The default table is TABLE_DIRECT mapping By far, most rules used work this way.
#   TABLE_R0 is rarely used.
#
#   The key K is then extracted from the subtree and used to find one
#   of the tables, T listed above.  The result after applying T[K] is
#   a format string and arguments (a la printf()) for the formatting
#   engine.
#
#   Escapes in the format string are:
#
#     %c  evaluate the node recursively. Its argument is a single
#         integer or tuple representing a node index.
#         If a tuple is given, the first item is the node index while
#         the second item is a string giving the node/noterminal name.
#         This name will be checked at runtime against the node type.
#
#     %p  like %c but sets the operator precedence.
#         Its argument then is a tuple indicating the node
#         index and the precidence value, an integer.
#
#     %C  evaluate children recursively, with sibling children separated by the
#         given string.  It needs a 3-tuple: a starting node, the maximimum
#         value of an end node, and a string to be inserted between sibling children
#
#     %,  Append ',' if last %C only printed one item. This is mostly for tuples
#         on the LHS of an assignment statement since BUILD_TUPLE_n pretty-prints
#         other tuples. The specifier takes no arguments
#
#     %P same as %C but sets operator precedence.  Its argument is a 4-tuple:
#         the node low and high indices, the separator, a string the precidence
#         value, an integer.
#
#     %D Same as `%C` this is for left-recursive lists like kwargs where goes
#         to epsilon at the beginning. It needs a 3-tuple: a starting node, the
#         maximimum value of an end node, and a string to be inserted between
#         sibling children. If we were to use `%C` an extra separator with an
#         epsilon would appear at the beginning.
#
#     %|  Insert spaces to the current indentation level. Takes no arguments.
#
#     %+ increase current indentation level. Takes no arguments.
#
#     %- decrease current indentation level. Takes no arguments.
#
#     %{...} evaluate ... in context of N
#
#     %% literal '%'. Takes no arguments.
#
#
#   The '%' may optionally be followed by a number (C) in square
#   brackets, which makes the template_engine walk down to N[C] before
#   evaluating the escape code.

import sys
IS_PYPY = '__pypy__' in sys.builtin_module_names
PYTHON3 = (sys.version_info >= (3, 0))

from xdis.code import iscode
from xdis.util import COMPILER_FLAG_BIT

from uncompyle6.parser import get_python_parser
from uncompyle6.parsers.treenode import SyntaxTree
from spark_parser import GenericASTTraversal, DEFAULT_DEBUG as PARSER_DEFAULT_DEBUG
from uncompyle6.scanner import Code, get_scanner
import uncompyle6.parser as python_parser
from uncompyle6.semantics.make_function import (
    make_function2, make_function3
    )
from uncompyle6.semantics.parser_error import ParserError
from uncompyle6.semantics.check_ast import checker
from uncompyle6.semantics.customize import customize_for_version
from uncompyle6.semantics.helper import (
    print_docstring, find_globals_and_nonlocals, flatten_list)
from uncompyle6.scanners.tok import Token

from uncompyle6.semantics.consts import (
    LINE_LENGTH, RETURN_LOCALS, NONE, RETURN_NONE, PASS,
    ASSIGN_DOC_STRING, NAME_MODULE, TAB,
    INDENT_PER_LEVEL, TABLE_R, MAP_DIRECT,
    MAP, PRECEDENCE, ASSIGN_TUPLE_PARAM, escape, minint)


from uncompyle6.show import (
    maybe_show_tree,
)

if PYTHON3:
    from io import StringIO
else:
    from StringIO import StringIO

def is_docstring(node):
    try:
        return (node[0][0].kind == 'assign' and
            node[0][0][1][0].pattr == '__doc__')
    except:
        return False

class SourceWalkerError(Exception):
    def __init__(self, errmsg):
        self.errmsg = errmsg

    def __str__(self):
        return self.errmsg

class SourceWalker(GenericASTTraversal, object):
    stacked_params = ('f', 'indent', 'is_lambda', '_globals')

    def __init__(self, version, out, scanner, showast=False,
                 debug_parser=PARSER_DEFAULT_DEBUG,
                 compile_mode='exec', is_pypy=IS_PYPY,
                 linestarts={}, tolerate_errors=False):
        """`version' is the Python version (a float) of the Python dialect
        of both the syntax tree and language we should produce.

        `out' is IO-like file pointer to where the output should go. It
        whould have a getvalue() method.

        `scanner' is a method to call when we need to scan tokens. Sometimes
        in producing output we will run across further tokens that need
        to be scaned.

        If `showast' is True, we print the syntax tree.

        `compile_mode' is is either 'exec' or 'single'. It isthe compile
        mode that was used to create the Syntax Tree and specifies a
        gramar variant within a Python version to use.

        `is_pypy' should be True if the Syntax Tree was generated for PyPy.

        `linestarts' is a dictionary of line number to bytecode offset. This
        can sometimes assist in determinte which kind of source-code construct
        to use when there is ambiguity.

        """
        GenericASTTraversal.__init__(self, ast=None)
        self.scanner = scanner
        params = {
            'f': out,
            'indent': '',
            }
        self.version = version
        self.p = get_python_parser(version, debug_parser=dict(debug_parser),
                                   compile_mode=compile_mode, is_pypy=is_pypy)
        self.debug_parser = dict(debug_parser)
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
        self.linestarts = linestarts
        self.line_number = 1
        self.ast_errors = []
        # FIXME: have p.insts update in a better way
        # modularity is broken here
        self.p.insts = scanner.insts

        # This is in Python 2.6 on. It changes the way
        # strings get interpreted. See n_LOAD_CONST
        self.FUTURE_UNICODE_LITERALS = False

        # Sometimes we may want to continue decompiling when there are errors
        # and sometimes not
        self.tolerate_errors = tolerate_errors

        # hide_internal suppresses displaying the additional instructions that sometimes
        # exist in code but but were not written in the source code.
        # An example is:
        # __module__ = __name__
        self.hide_internal = True
        self.name = None
        self.version = version
        self.is_pypy = is_pypy
        customize_for_version(self, is_pypy, version)

        return

    def str_with_template(self, ast):
        stream = sys.stdout
        stream.write(self.str_with_template1(ast, '', None))
        stream.write('\n')

    def str_with_template1(self, ast, indent, sibNum=None):
        rv = str(ast.kind)

        if sibNum is not None:
            rv = "%2d. %s" % (sibNum, rv)
        enumerate_children = False
        if len(ast) > 1:
            rv += " (%d)" % (len(ast))
            enumerate_children = True

        mapping = self._get_mapping(ast)
        table = mapping[0]
        key = ast
        for i in mapping[1:]:
            key = key[i]
            pass

        if key.kind in table:
            rv += ": %s" % str(table[key.kind])

        rv = indent + rv
        indent += '    '
        i = 0
        for node in ast:
            if hasattr(node, '__repr1__'):
                if enumerate_children:
                    child =  self.str_with_template1(node, indent, i)
                else:
                    child = self.str_with_template1(node, indent, None)
            else:
                inst = node.format(line_prefix='L.')
                if inst.startswith("\n"):
                    # Nuke leading \n
                    inst = inst[1:]
                if enumerate_children:
                    child = indent + "%2d. %s" % (i, inst)
                else:
                    child = indent + inst
                pass
            rv += "\n" + child
            i += 1
        return rv


    def indent_if_source_nl(self, line_number, indent):
        if (line_number != self.line_number):
            self.write("\n" + self.indent + INDENT_PER_LEVEL[:-1])
        return self.line_number

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

    def set_pos_info(self, node):
        if hasattr(node, 'linestart') and node.linestart:
            self.line_number = node.linestart

    def preorder(self, node=None):
        super(SourceWalker, self).preorder(node)
        self.set_pos_info(node)

    def indent_more(self, indent=TAB):
        self.indent += indent

    def indent_less(self, indent=TAB):
        self.indent = self.indent[:-len(indent)]

    def traverse(self, node, indent=None, is_lambda=False):
        self.param_stack.append(self.params)
        if indent is None: indent = self.indent
        p = self.pending_newlines
        self.pending_newlines = 0
        self.params = {
            '_globals': {},
            '_nonlocals': {},   # Python 3 has nonlocal
            'f': StringIO(),
            'indent': indent,
            'is_lambda': is_lambda,
            }
        self.preorder(node)
        self.f.write('\n'*self.pending_newlines)
        result = self.f.getvalue()
        self.params = self.param_stack.pop()
        self.pending_newlines = p
        return result

    def write(self, *data):
        if (len(data) == 0) or (len(data) == 1 and data[0] == ''):
            return
        out = ''.join((str(j) for j in data))
        n = 0
        for i in out:
            if i == '\n':
                n += 1
                if n == len(out):
                    self.pending_newlines = max(self.pending_newlines, n)
                    return
            elif n:
                self.pending_newlines = max(self.pending_newlines, n)
                out = out[n:]
                break
            else:
                break

        if self.pending_newlines > 0:
            self.f.write('\n'*self.pending_newlines)
            self.pending_newlines = 0

        for i in out[::-1]:
            if i == '\n':
                self.pending_newlines += 1
            else:
                break

        if self.pending_newlines:
            out = out[:-self.pending_newlines]
        if (isinstance(out, str) and
             not (PYTHON3 or self.FUTURE_UNICODE_LITERALS)):
            out = unicode(out, 'utf-8')
        self.f.write(out)

    def println(self, *data):
        if data and not(len(data) == 1 and data[0] ==''):
            self.write(*data)
        self.pending_newlines = max(self.pending_newlines, 1)

    def is_return_none(self, node):
        # Is there a better way?
        ret = (node[0] == 'ret_expr'
               and node[0][0] == 'expr'
               and node[0][0][0] == 'LOAD_CONST'
               and node[0][0][0].pattr is None)
        if self.version <= 2.6:
            return ret
        else:
            # FIXME: should the SyntaxTree expression be folded into
            # the global RETURN_NONE constant?
            return (ret or
                    node == SyntaxTree('return',
                                [SyntaxTree('ret_expr', [NONE]), Token('RETURN_VALUE')]))

    # Python 3.x can have be dead code as a result of its optimization?
    # So we'll add a # at the end of the return lambda so the rest is ignored
    def n_return_lambda(self, node):
        if 1 <= len(node) <= 2:
            self.preorder(node[0])
            self.write(' # Avoid dead code: ')
            self.prune()
        else:
            # We can't comment out like above because there may be a trailing ')'
            # that needs to be written
            assert len(node) == 3 and node[2] == 'LAMBDA_MARKER'
            self.preorder(node[0])
            self.prune()

    def n_return(self, node):
        if self.params['is_lambda']:
            self.preorder(node[0])
            self.prune()
        else:
            self.write(self.indent, 'return')
            # One reason we worry over whether we use "return None" or "return"
            # is that inside a generator, "return None" is illegal.
            # Thank you, Python!
            if (self.return_none or not self.is_return_none(node)):
                self.write(' ')
                self.preorder(node[0])
            self.println()
            self.prune() # stop recursing

    def n_return_if_stmt(self, node):
        if self.params['is_lambda']:
            self.write(' return ')
            self.preorder(node[0])
            self.prune()
        else:
            self.write(self.indent, 'return')
            if self.return_none or not self.is_return_none(node):
                self.write(' ')
                self.preorder(node[0])
            self.println()
            self.prune() # stop recursing

    def n_yield(self, node):
        if node != SyntaxTree('yield', [NONE, Token('YIELD_VALUE')]):
            self.template_engine(( 'yield %c', 0), node)
        elif self.version <= 2.4:
            # Early versions of Python don't allow a plain "yield"
            self.write('yield None')
        else:
            self.write('yield')

        self.prune() # stop recursing

    def n_build_slice3(self, node):
        p = self.prec
        self.prec = 100
        if not node[0].isNone():
            self.preorder(node[0])
        self.write(':')
        if not node[1].isNone():
            self.preorder(node[1])
        self.write(':')
        if not node[2].isNone():
            self.preorder(node[2])
        self.prec = p
        self.prune() # stop recursing

    def n_build_slice2(self, node):
        p = self.prec
        self.prec = 100
        if not node[0].isNone():
            self.preorder(node[0])
        self.write(':')
        if not node[1].isNone():
            self.preorder(node[1])
        self.prec = p
        self.prune() # stop recursing

    def n_expr(self, node):
        p = self.prec
        if node[0].kind.startswith('binary_expr'):
            n = node[0][-1][0]
        else:
            n = node[0]

        # if (hasattr(n, 'linestart') and n.linestart and
        #     hasattr(self, 'current_line_number')):
        #     self.source_linemap[self.current_line_number] = n.linestart

        self.prec = PRECEDENCE.get(n.kind, -2)
        if n == 'LOAD_CONST' and repr(n.pattr)[0] == '-':
            self.prec = 6

        if p < self.prec:
            self.write('(')
            self.preorder(node[0])
            self.write(')')
        else:
            self.preorder(node[0])
        self.prec = p
        self.prune()

    def n_ret_expr(self, node):
        if len(node) == 1 and node[0] == 'expr':
            self.n_expr(node[0])
        else:
            self.n_expr(node)

    n_ret_expr_or_cond = n_expr

    def n_binary_expr(self, node):
        self.preorder(node[0])
        self.write(' ')
        self.preorder(node[-1])
        self.write(' ')
        self.prec -= 1
        self.preorder(node[1])
        self.prec += 1
        self.prune()

    def n_str(self, node):
        self.write(node[0].pattr)
        self.prune()

    def pp_tuple(self, tup):
        """Pretty print a tuple"""
        last_line = self.f.getvalue().split("\n")[-1]
        l = len(last_line)+1
        indent = ' ' * l
        self.write('(')
        sep = ''
        for item in tup:
            self.write(sep)
            l += len(sep)
            s = repr(item)
            l += len(s)
            self.write(s)
            sep = ','
            if l > LINE_LENGTH:
                l = 0
                sep += '\n' + indent
            else:
                sep += ' '
                pass
            pass
        if len(tup) == 1:
            self.write(", ")
        self.write(')')

    def n_LOAD_CONST(self, node):
        attr = node.attr
        data = node.pattr; datatype = type(data)
        if isinstance(data, float) and str(data) in frozenset(['nan', '-nan', 'inf', '-inf']):
            # float values 'nan' and 'inf' are not directly representable in Python at least
            # before 3.5 and even there it is via a library constant.
            # So we will canonicalize their representation as float('nan') and float('inf')
            self.write("float('%s')" % data)
        elif isinstance(datatype, int) and data == minint:
            # convert to hex, since decimal representation
            # would result in 'LOAD_CONST; UNARY_NEGATIVE'
            # change:hG/2002-02-07: this was done for all negative integers
            # todo: check whether this is necessary in Python 2.1
            self.write( hex(data) )
        elif datatype is type(Ellipsis):
            self.write('...')
        elif attr is None:
            # LOAD_CONST 'None' only occurs, when None is
            # implicit eg. in 'return' w/o params
            # pass
            self.write('None')
        elif isinstance(data, tuple):
            self.pp_tuple(data)
        elif isinstance(attr, bool):
            self.write(repr(attr))
        elif self.FUTURE_UNICODE_LITERALS:
            # The FUTURE_UNICODE_LITERALS compiler flag
            # in 2.6 on change the way
            # strings are interpreted:
            #    u'xxx' -> 'xxx'
            #    xxx'   -> b'xxx'
            if not PYTHON3 and isinstance(data, unicode):
                try:
                    data = str(data)
                except UnicodeEncodeError:
                    # Have to keep data as it is: in Unicode.
                    pass
                self.write(repr(data))
            elif isinstance(data, str):
                self.write('b'+repr(data))
            else:
                self.write(repr(data))
        else:
            self.write(repr(data))
        # LOAD_CONST is a terminal, so stop processing/recursing early
        self.prune()

    def n_delete_subscr(self, node):
        if node[-2][0] == 'build_list' and node[-2][0][-1].kind.startswith('BUILD_TUPLE'):
            if node[-2][0][-1] != 'BUILD_TUPLE_0':
                node[-2][0].kind = 'build_tuple2'
        self.default(node)

    n_store_subscr = n_subscript = n_delete_subscr

    # Note: this node is only in Python 2.x
    # FIXME: figure out how to get this into customization
    # put so that we can get access via super from
    # the fragments routine.
    def n_exec_stmt(self, node):
        """
        exec_stmt ::= expr exprlist DUP_TOP EXEC_STMT
        exec_stmt ::= expr exprlist EXEC_STMT
        """
        self.write(self.indent, 'exec ')
        self.preorder(node[0])
        if not node[1][0].isNone():
            sep = ' in '
            for subnode in node[1]:
                self.write(sep); sep = ", "
                self.preorder(subnode)
        self.println()
        self.prune() # stop recursing

    def n_ifelsestmt(self, node, preprocess=False):
        else_suite = node[3]

        n = else_suite[0]

        if len(n) == 1 == len(n[0]) and n[0] == '_stmts':
            n = n[0][0][0]
        elif n[0].kind in ('lastc_stmt', 'lastl_stmt'):
            n = n[0][0]
        else:
            if not preprocess:
                self.default(node)
            return

        if n.kind in ('ifstmt', 'iflaststmt', 'iflaststmtl'):
            node.kind = 'ifelifstmt'
            n.kind = 'elifstmt'
        elif n.kind in ('ifelsestmtr',):
            node.kind = 'ifelifstmt'
            n.kind = 'elifelsestmtr'
        elif n.kind in ('ifelsestmt', 'ifelsestmtc', 'ifelsestmtl'):
            node.kind = 'ifelifstmt'
            self.n_ifelsestmt(n, preprocess=True)
            if n == 'ifelifstmt':
                n.kind = 'elifelifstmt'
            elif n.kind in ('ifelsestmt', 'ifelsestmtc', 'ifelsestmtl'):
                n.kind = 'elifelsestmt'
        if not preprocess:
            self.default(node)

    n_ifelsestmtc = n_ifelsestmtl = n_ifelsestmt

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

        self.write(self.indent, 'if ')
        self.preorder(node[0])
        self.println(':')
        self.indent_more()
        self.preorder(node[1])
        self.indent_less()

        if_ret_at_end = False
        if len(return_stmts_node[0]) >= 3:
            if (return_stmts_node[0][-1][0] == 'ifstmt'
                and return_stmts_node[0][-1][0][1][0] == 'return_if_stmts'):
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
            self.preorder(n)
        if not past_else or if_ret_at_end:
            self.println(self.indent, 'else:')
            self.indent_more()
        self.preorder(return_stmts_node[1])
        self.indent_less()
        self.prune()
    n_ifelsestmtr2 = n_ifelsestmtr

    def n_elifelsestmtr(self, node):
        if node[2] == 'COME_FROM':
            return_stmts_node = node[3]
            node.kind = 'elifelsestmtr2'
        else:
            return_stmts_node = node[2]

        if len(return_stmts_node) != 2:
            self.default(node)

        for n in return_stmts_node[0]:
            if not (n[0] == 'ifstmt' and n[0][1][0] == 'return_if_stmts'):
                self.default(node)
                return

        self.write(self.indent, 'elif ')
        self.preorder(node[0])
        self.println(':')
        self.indent_more()
        self.preorder(node[1])
        self.indent_less()

        for n in return_stmts_node[0]:
            n[0].kind = 'elifstmt'
            self.preorder(n)
        self.println(self.indent, 'else:')
        self.indent_more()
        self.preorder(return_stmts_node[1])
        self.indent_less()
        self.prune()

    def n_alias(self, node):
        if self.version <= 2.1:
            if len(node) == 2:
                store = node[1]
                assert store == 'store'
                if store[0].pattr == node[0].pattr:
                    self.write("import %s\n" % node[0].pattr)
                else:
                    self.write("import %s as %s\n" %
                               (node[0].pattr, store[0].pattr))
                    pass
                pass
            self.prune() # stop recursing


        store_node = node[-1][-1]
        assert store_node.kind.startswith('STORE_')
        iname = node[0].pattr  # import name
        sname = store_node.pattr # store_name
        if iname and iname == sname or iname.startswith(sname + '.'):
            self.write(iname)
        else:
            self.write(iname, ' as ', sname)
        self.prune() # stop recursing

    def n_import_from(self, node):
        relative_path_index = 0
        if self.version >= 2.5:
            if node[relative_path_index].pattr > 0:
                node[2].pattr = ('.' * node[relative_path_index].pattr) + node[2].pattr
            if self.version > 2.7:
                if isinstance(node[1].pattr, tuple):
                    imports = node[1].pattr
                    for pattr in imports:
                        node[1].pattr = pattr
                        self.default(node)
                    return
                pass
        self.default(node)

    n_import_from_star = n_import_from

    def n_mkfunc(self, node):

        if self.version >= 3.3 or node[-2] in ('kwargs', 'no_kwargs'):
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

        self.indent_more()
        self.make_function(node, is_lambda=False, code_node=code_node)

        if len(self.param_stack) > 1:
            self.write('\n\n')
        else:
            self.write('\n\n\n')
        self.indent_less()
        self.prune() # stop recursing

    def make_function(self, node, is_lambda, nested=1,
                      code_node=None, annotate=None):
        if self.version >= 3.0:
            make_function3(self, node, is_lambda, nested, code_node)
        else:
            make_function2(self, node, is_lambda, nested, code_node)

    def n_mklambda(self, node):
        self.make_function(node, is_lambda=True, code_node=node[-2])
        self.prune() # stop recursing

    def n_list_comp(self, node):
        """List comprehensions"""
        p = self.prec
        self.prec = 100
        if self.version >= 2.7:
            if self.is_pypy:
                self.n_list_comp_pypy27(node)
                return
            n = node[-1]
        elif node[-1] == 'del_stmt':
            if node[-2] == 'JUMP_BACK':
                n = node[-3]
            else:
                n = node[-2]

        assert n == 'list_iter'

        # Find the list comprehension body. It is the inner-most
        # node that is not list_.. .
        # FIXME: DRY with other use
        while n == 'list_iter':
            n = n[0]  # iterate one nesting deeper
            if   n == 'list_for':	n = n[3]
            elif n == 'list_if':	n = n[2]
            elif n == 'list_if_not': n= n[2]
        assert n == 'lc_body'
        self.write( '[ ')

        if self.version >= 2.7:
            expr = n[0]
            list_iter = node[-1]
        else:
            expr = n[1]
            if node[-2] == 'JUMP_BACK':
                list_iter = node[-3]
            else:
                list_iter = node[-2]

        assert expr == 'expr'
        assert list_iter == 'list_iter'

        # FIXME: use source line numbers for directing line breaks

        line_number = self.line_number
        last_line = self.f.getvalue().split("\n")[-1]
        l = len(last_line)
        indent = ' ' * (l-1)

        self.preorder(expr)
        line_number = self.indent_if_source_nl(line_number, indent)
        self.preorder(list_iter)
        l2 = self.indent_if_source_nl(line_number, indent)
        if l2 != line_number:
            self.write(' ' * (len(indent) - len(self.indent) - 1) + ']')
        else:
            self.write( ' ]')
        self.prec = p
        self.prune() # stop recursing

    def n_list_comp_pypy27(self, node):
        """List comprehensions in PYPY."""
        p = self.prec
        self.prec = 27
        if node[-1].kind == 'list_iter':
            n = node[-1]
        elif self.is_pypy and node[-1] == 'JUMP_BACK':
            n = node[-2]
        list_expr = node[1]

        if len(node) >= 3:
            store = node[3]
        elif self.is_pypy and n[0] == 'list_for':
            store = n[0][2]

        assert n == 'list_iter'
        assert store == 'store'

        # Find the list comprehension body. It is the inner-most
        # node.
        # FIXME: DRY with other use
        while n == 'list_iter':
            n = n[0] # iterate one nesting deeper
            if   n == 'list_for':	n = n[3]
            elif n == 'list_if':	n = n[2]
            elif n == 'list_if_not': n= n[2]
        assert n == 'lc_body'
        self.write( '[ ')

        expr = n[0]
        if self.is_pypy and node[-1] == 'JUMP_BACK':
            list_iter = node[-2]
        else:
            list_iter = node[-1]

        assert expr == 'expr'
        assert list_iter == 'list_iter'

        # FIXME: use source line numbers for directing line breaks

        self.preorder(expr)
        self.preorder(list_expr)
        self.write( ' ]')
        self.prec = p
        self.prune() # stop recursing

    def comprehension_walk(self, node, iter_index, code_index=-5):
        p = self.prec
        self.prec = 27

        # FIXME: clean this up
        if self.version >= 3.0 and node == 'dict_comp':
            cn = node[1]
        elif self.version < 2.7 and node == 'generator_exp':
            if node[0] == 'LOAD_GENEXPR':
                cn = node[0]
            elif node[0] == 'load_closure':
                cn = node[1]

        elif self.version >= 3.0 and node == 'generator_exp':
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
        assert n == 'comp_iter', n

        # Find the comprehension body. It is the inner-most
        # node that is not list_.. .
        while n == 'comp_iter': # list_iter
            n = n[0] # recurse one step
            if n == 'comp_for':
                if n[0] == 'SETUP_LOOP':
                    n = n[4]
                else:
                    n = n[3]
            elif n == 'comp_if':
                n = n[2]
            elif n == 'comp_if_not':
                n = n[2]

        assert n == 'comp_body', n

        self.preorder(n[0])
        self.write(' for ')
        self.preorder(ast[iter_index-1])
        self.write(' in ')
        if node[2] == 'expr':
            iter_expr = node[2]
        else:
            iter_expr = node[-3]
        assert iter_expr == 'expr'
        self.preorder(iter_expr)
        self.preorder(ast[iter_index])
        self.prec = p

    def n_generator_exp(self, node):
        self.write('(')
        if self.version > 3.2:
            code_index = -6
        else:
            code_index = -5
        self.comprehension_walk(node, iter_index=3, code_index=code_index)
        self.write(')')
        self.prune()

    def n_set_comp(self, node):
        self.write('{')
        if node[0] in ['LOAD_SETCOMP', 'LOAD_DICTCOMP']:
            self.comprehension_walk_newer(node, 1, 0)
        elif node[0].kind == 'load_closure' and self.version >= 3.0:
            self.setcomprehension_walk3(node, collection_index=4)
        else:
            self.comprehension_walk(node, iter_index=4)
        self.write('}')
        self.prune()
    n_dict_comp = n_set_comp

    def comprehension_walk_newer(self, node, iter_index, code_index=-5):
        """Non-closure-based comprehensions the way they are done in Python3
        and some Python 2.7. Note: there are also other set comprehensions.
        """
        p = self.prec
        self.prec = 27
        code = node[code_index].attr

        assert iscode(code), node[code_index]
        code = Code(code, self.scanner, self.currentclass)

        ast = self.build_ast(code._tokens, code._customize)
        self.customize(code._customize)

        # skip over: sstmt, stmt, return, ret_expr
        # and other singleton derivations
        while (len(ast) == 1
               or (ast in ('sstmt', 'return')
                   and ast[-1] in ('RETURN_LAST', 'RETURN_VALUE'))):
            self.prec=100
            ast = ast[0]

        # Pick out important parts of the comprehension:
        # * the variable we interate over: "store"
        # * the results we accumulate: "n"

        is_30_dict_comp = False
        store = None
        n = ast[iter_index]
        if ast in ('set_comp_func', 'dict_comp_func',
                   'list_comp', 'set_comp_func_header'):
            for k in ast:
                if k == 'comp_iter':
                    n = k
                elif k == 'store':
                    store = k
                    pass
                pass
            pass
        elif ast in ('dict_comp', 'set_comp'):
            assert self.version == 3.0
            for k in ast:
                if k in ('dict_comp_header', 'set_comp_header'):
                    n = k
                elif k == 'store':
                    store = k
                elif k == 'dict_comp_iter':
                    is_30_dict_comp = True
                    n = (k[3], k[1])
                    pass
                elif k == 'comp_iter':
                    n = k[1]
                    pass
                pass
        else:
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
            # iterate one nesting deeper
            if self.version == 3.0 and len(n) == 3:
                assert n[0] == 'expr' and n[1] == 'expr'
                n = n[1]
            else:
                n = n[0]

            if n in ('list_for', 'comp_for'):
                if n[2] == 'store':
                    store = n[2]
                n = n[3]
            elif n in ('list_if', 'list_if_not', 'comp_if', 'comp_if_not'):
                have_not = n in ('list_if_not', 'comp_if_not')
                if_node = n[0]
                if n[1] == 'store':
                    store = n[1]
                n = n[2]
                pass
            pass

        # Python 2.7+ starts including set_comp_body
        # Python 3.5+ starts including set_comp_func
        # Python 3.0  is yet another snowflake
        if self.version != 3.0:
            assert n.kind in ('lc_body', 'comp_body', 'set_comp_func', 'set_comp_body'), ast
        assert store, "Couldn't find store in list/set comprehension"

        # A problem created with later Python code generation is that there
        # is a lamda set up with a dummy argument name that is then called
        # So we can't just translate that as is but need to replace the
        # dummy name. Below we are picking out the variable name as seen
        # in the code. And trying to generate code for the other parts
        # that don't have the dummy argument name in it.
        # Another approach might be to be able to pass in the source name
        # for the dummy argument.

        if is_30_dict_comp:
            self.preorder(n[0])
            self.write(': ')
            self.preorder(n[1])
        else:
            self.preorder(n[0])
        self.write(' for ')
        if comp_store:
            self.preorder(comp_store)
        else:
            self.preorder(store)

        # FIXME this is all merely approximate
        self.write(' in ')
        self.preorder(node[-3])

        if ast == 'list_comp' and self.version != 3.0:
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

    def listcomprehension_walk2(self, node):
        """List comprehensions the way they are done in Python 2 and
        sometimes in Python 3.
        They're more other comprehensions, e.g. set comprehensions
        See if we can combine code.
        """
        p = self.prec
        self.prec = 27

        code = Code(node[1].attr, self.scanner, self.currentclass)
        ast = self.build_ast(code._tokens, code._customize)
        self.customize(code._customize)

        # skip over: sstmt, stmt, return, ret_expr
        # and other singleton derivations
        while (len(ast) == 1
               or (ast in ('sstmt', 'return')
                   and ast[-1] in ('RETURN_LAST', 'RETURN_VALUE'))):
            self.prec=100
            ast = ast[0]

        n = ast[1]
        # collection = node[-3]
        collections = [node[-3]]
        list_ifs = []

        if self.version == 3.0 and n != 'list_iter':
            # FIXME 3.0 is a snowflake here. We need
            # special code for this. Not sure if this is totally
            # correct.
            stores = [ast[3]]
            assert ast[4] == 'comp_iter'
            n = ast[4]
            # Find the list comprehension body. It is the inner-most
            # node that is not comp_.. .
            while n == 'comp_iter':
                if n[0] == 'comp_for':
                    n = n[0]
                    stores.append(n[2])
                    n = n[3]
                elif n[0] in ('comp_if', 'comp_if_not'):
                    n = n[0]
                    # FIXME: just a guess
                    if n[0].kind == 'expr':
                        list_ifs.append(n)
                    else:
                        list_ifs.append([1])
                    n = n[2]
                    pass
                else:
                    break
                pass

            # Skip over n[0] which is something like: _[1]
            self.preorder(n[1])

        else:
            assert n == 'list_iter'
            stores = []
            # Find the list comprehension body. It is the inner-most
            # node that is not list_.. .
            while n == 'list_iter':
                n = n[0] # recurse one step
                if n == 'list_for':
                    stores.append(n[2])
                    n = n[3]
                    if self.version >= 3.6 and n[0] == 'list_for':
                        # Dog-paddle down largely singleton reductions
                        # to find the collection (expr)
                        c = n[0][0]
                        if c == 'expr':
                            c = c[0]
                        # FIXME: grammar is wonky here? Is this really an attribute?
                        if c == 'attribute':
                            c = c[0]
                        collections.append(c)
                        pass
                elif n in ('list_if', 'list_if_not'):
                    # FIXME: just a guess
                    if n[0].kind == 'expr':
                        list_ifs.append(n)
                    else:
                        list_ifs.append([1])
                    n = n[2]
                    pass
                pass

            assert n == 'lc_body', ast
            self.preorder(n[0])

        # FIXME: add indentation around "for"'s and "in"'s
        if self.version < 3.6:
            self.write(' for ')
            self.preorder(stores[0])
            self.write(' in ')
            self.preorder(collections[0])
            if list_ifs:
                self.preorder(list_ifs[0])
                pass
        else:
            for i, store in enumerate(stores):
                self.write(' for ')
                self.preorder(store)
                self.write(' in ')
                self.preorder(collections[i])
                if i < len(list_ifs):
                    self.preorder(list_ifs[i])
                    pass
                pass
        self.prec = p

    def n_listcomp(self, node):
        self.write('[')
        if node[0].kind == 'load_closure':
            self.listcomprehension_walk2(node)
        else:
            self.comprehension_walk_newer(node, 1, 0)
        self.write(']')
        self.prune()

    def setcomprehension_walk3(self, node, collection_index):
        """Set comprehensions the way they are done in Python3.
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
        self.preorder(store)
        self.write(' in ')
        self.preorder(collection)
        if list_if:
            self.preorder(list_if)
        self.prec = p

    def n_classdef(self, node):

        if self.version >= 3.0:
            self.n_classdef3(node)

        # class definition ('class X(A,B,C):')
        cclass = self.currentclass

        # Pick out various needed bits of information
        # * class_name - the name of the class
        # * subclass_info - the parameters to the class  e.g.
        #      class Foo(bar, baz)
        #             -----------
        # * subclass_code - the code for the subclass body

        if node == 'classdefdeco2':
            build_class = node
        else:
            build_class = node[0]
        build_list = build_class[1][0]
        if hasattr(build_class[-3][0], 'attr'):
            subclass_code = build_class[-3][0].attr
            class_name = build_class[0].pattr
        elif (build_class[-3] == 'mkfunc' and
              node == 'classdefdeco2' and
              build_class[-3][0] == 'load_closure'):
            subclass_code = build_class[-3][1].attr
            class_name = build_class[-3][0][0].pattr
        elif hasattr(node[0][0], 'pattr'):
            subclass_code = build_class[-3][1].attr
            class_name = node[0][0].pattr
        else:
            raise 'Internal Error n_classdef: cannot find class name'

        if (node == 'classdefdeco2'):
            self.write('\n')
        else:
            self.write('\n\n')

        self.currentclass = str(class_name)
        self.write(self.indent, 'class ', self.currentclass)

        self.print_super_classes(build_list)
        self.println(':')

        # class body
        self.indent_more()
        self.build_class(subclass_code)
        self.indent_less()

        self.currentclass = cclass
        if len(self.param_stack) > 1:
            self.write('\n\n')
        else:
            self.write('\n\n\n')

        self.prune()

    n_classdefdeco2 = n_classdef

    def print_super_classes(self, node):
        if not (node == 'tuple'):
            return

        n_subclasses = len(node[:-1])
        if n_subclasses > 0 or self.version > 2.4:
            # Not an old-style pre-2.2 class
            self.write('(')

        line_separator = ', '
        sep = ''
        for elem in node[:-1]:
            value = self.traverse(elem)
            self.write(sep, value)
            sep = line_separator

        if n_subclasses > 0 or self.version > 2.4:
            # Not an old-style pre-2.2 class
            self.write(')')

    def print_super_classes3(self, node):
        n = len(node) - 1
        if node.kind != 'expr':
            if node == 'kwarg':
                self.write('(')
                self.template_engine(('%[0]{pattr}=%c', 1), node)
                self.write(')')
                return

            kwargs = None
            assert node[n].kind.startswith('CALL_FUNCTION')

            if node[n].kind.startswith('CALL_FUNCTION_KW'):
                # 3.6+ starts does this
                kwargs = node[n-1].attr
                assert isinstance(kwargs, tuple)
                i = n - (len(kwargs)+1)
                j = 1 + n - node[n].attr
            else:
                start = n-2
                for i in range(start, 0, -1):
                    if not node[i].kind in ['expr', 'call', 'LOAD_CLASSNAME']:
                        break
                    pass

                if i == start:
                    return
                i += 2

            line_separator = ', '
            sep = ''
            self.write('(')
            if kwargs:
                # Last arg is tuple of keyword values: omit
                l = n - 1
            else:
                l = n

            if kwargs:
                # 3.6+ does this
                while j < i:
                    self.write(sep)
                    value = self.traverse(node[j])
                    self.write("%s" % value)
                    sep = line_separator
                    j += 1

                j = 0
                while i < l:
                    self.write(sep)
                    value = self.traverse(node[i])
                    self.write("%s=%s" % (kwargs[j], value))
                    sep = line_separator
                    j += 1
                    i += 1
            else:
                while i < l:
                    value = self.traverse(node[i])
                    i += 1
                    self.write(sep, value)
                    sep = line_separator
                    pass
            pass
        else:
            if self.version >= 3.6 and node[0] == 'LOAD_CONST':
                return
            value = self.traverse(node[0])
            self.write('(')
            self.write(value)
            pass

        self.write(')')

    def n_dict(self, node):
        """
        prettyprint a dict
        'dict' is something like k = {'a': 1, 'b': 42}"
        We will source-code use line breaks to guide us when to break.
        """
        p = self.prec
        self.prec = 100

        self.indent_more(INDENT_PER_LEVEL)
        sep = INDENT_PER_LEVEL[:-1]
        if node[0] != 'dict_entry':
            self.write('{')
        line_number = self.line_number

        if self.version >= 3.0 and not self.is_pypy:
            if node[0].kind.startswith('kvlist'):
                # Python 3.5+ style key/value list in dict
                kv_node = node[0]
                l = list(kv_node)
                length = len(l)
                if kv_node[-1].kind.startswith("BUILD_MAP"):
                    length -= 1
                i = 0

                # Respect line breaks from source
                while i < length:
                    self.write(sep)
                    name = self.traverse(l[i], indent='')
                    if i > 0:
                        line_number = self.indent_if_source_nl(line_number,
                                                               self.indent + INDENT_PER_LEVEL[:-1])
                    line_number = self.line_number
                    self.write(name, ': ')
                    value = self.traverse(l[i+1], indent=self.indent+(len(name)+2)*' ')
                    self.write(value)
                    sep = ", "
                    if line_number != self.line_number:
                        sep += "\n" + self.indent + INDENT_PER_LEVEL[:-1]
                        line_number = self.line_number
                    i += 2
                    pass
                pass
            elif len(node) > 1 and node[1].kind.startswith('kvlist'):
                # Python 3.0..3.4 style key/value list in dict
                kv_node = node[1]
                l = list(kv_node)
                if len(l) > 0 and l[0].kind == 'kv3':
                    # Python 3.2 does this
                    kv_node = node[1][0]
                    l = list(kv_node)
                i = 0
                while i < len(l):
                    self.write(sep)
                    name = self.traverse(l[i+1], indent='')
                    if i > 0:
                        line_number = self.indent_if_source_nl(line_number,
                                                               self.indent + INDENT_PER_LEVEL[:-1])
                        pass
                    line_number = self.line_number
                    self.write(name, ': ')
                    value = self.traverse(l[i], indent=self.indent+(len(name)+2)*' ')
                    self.write(value)
                    sep = ", "
                    if line_number != self.line_number:
                        sep += "\n" + self.indent + INDENT_PER_LEVEL[:-1]
                        line_number = self.line_number
                    else:
                        sep += " "
                    i += 3
                    pass
                pass
            elif node[-1].kind.startswith('BUILD_CONST_KEY_MAP'):
                # Python 3.6+ style const map
                keys = node[-2].pattr
                values = node[:-2]
                # FIXME: Line numbers?
                for key, value in zip(keys, values):
                    self.write(sep)
                    self.write(repr(key))
                    line_number = self.line_number
                    self.write(':')
                    self.write(self.traverse(value[0]))
                    sep = ", "
                    if line_number != self.line_number:
                        sep += "\n" + self.indent + INDENT_PER_LEVEL[:-1]
                        line_number = self.line_number
                    else:
                        sep += " "
                        pass
                    pass
                if sep.startswith(",\n"):
                    self.write(sep[1:])
                pass
            elif node[0].kind.startswith('dict_entry'):
                assert self.version >= 3.5
                template = ("%C", (0, len(node[0]), ", **"))
                self.template_engine(template, node[0])
                sep = ''
            elif (node[-1].kind.startswith('BUILD_MAP_UNPACK')
                  or node[-1].kind.startswith('dict_entry')):
                assert self.version >= 3.5
                # FIXME: I think we can intermingle dict_comp's with other
                # dictionary kinds of things. The most common though is
                # a sequence of dict_comp's
                kwargs = node[-1].attr
                template = ("**%C", (0, kwargs, ", **"))
                self.template_engine(template, node)
                sep = ''

            pass
        else:
            # Python 2 style kvlist. Find beginning of kvlist.
            if node[0].kind.startswith("BUILD_MAP"):
                if len(node) > 1 and node[1].kind in ('kvlist', 'kvlist_n'):
                    kv_node = node[1]
                else:
                    kv_node = node[1:]
            else:
                assert node[-1].kind.startswith('kvlist')
                kv_node = node[-1]

            first_time = True
            for kv in kv_node:
                assert kv in ('kv', 'kv2', 'kv3')

                # kv ::= DUP_TOP expr ROT_TWO expr STORE_SUBSCR
                # kv2 ::= DUP_TOP expr expr ROT_THREE STORE_SUBSCR
                # kv3 ::= expr expr STORE_MAP

                # FIXME: DRY this and the above
                indent = self.indent + "  "
                if kv == 'kv':
                    self.write(sep)
                    name = self.traverse(kv[-2], indent='')
                    if first_time:
                        line_number = self.indent_if_source_nl(line_number, indent)
                        first_time = False
                        pass
                    line_number = self.line_number
                    self.write(name, ': ')
                    value = self.traverse(kv[1], indent=self.indent+(len(name)+2)*' ')
                elif kv == 'kv2':
                    self.write(sep)
                    name = self.traverse(kv[1], indent='')
                    if first_time:
                        line_number = self.indent_if_source_nl(line_number, indent)
                        first_time = False
                        pass
                    line_number = self.line_number
                    self.write(name, ': ')
                    value = self.traverse(kv[-3], indent=self.indent+(len(name)+2)*' ')
                elif kv == 'kv3':
                    self.write(sep)
                    name = self.traverse(kv[-2], indent='')
                    if first_time:
                        line_number = self.indent_if_source_nl(line_number, indent)
                        first_time = False
                        pass
                    line_number = self.line_number
                    self.write(name, ': ')
                    line_number = self.line_number
                    value = self.traverse(kv[0], indent=self.indent+(len(name)+2)*' ')
                    pass
                self.write(value)
                sep = ", "
                if line_number != self.line_number:
                    sep += "\n" + self.indent + "  "
                    line_number = self.line_number
                    pass
                pass
            pass
        if sep.startswith(",\n"):
            self.write(sep[1:])
        if node[0] != 'dict_entry':
            self.write('}')
        self.indent_less(INDENT_PER_LEVEL)
        self.prec = p
        self.prune()

    def n_list(self, node):
        """
        prettyprint a list or tuple
        """
        p = self.prec
        self.prec = 100
        lastnode = node.pop()
        lastnodetype = lastnode.kind

        # If this build list is inside a CALL_FUNCTION_VAR,
        # then the first * has already been printed.
        # Until I have a better way to check for CALL_FUNCTION_VAR,
        # will assume that if the text ends in *.
        last_was_star = self.f.getvalue().endswith('*')

        if lastnodetype.endswith('UNPACK'):
            # FIXME: need to handle range of BUILD_LIST_UNPACK
            have_star = True
            # endchar = ''
        else:
            have_star = False

        if lastnodetype.startswith('BUILD_LIST'):
            self.write('['); endchar = ']'
        elif lastnodetype.startswith('BUILD_TUPLE'):
            # Tuples can appear places that can NOT
            # have parenthesis around them, like array
            # subscripts. We check for that by seeing
            # if a tuple item is some sort of slice.
            no_parens = False
            for n in node:
                if n == 'expr' and n[0].kind.startswith('build_slice'):
                    no_parens = True
                    break
                pass
            if no_parens:
                endchar = ''
            else:
                self.write('('); endchar = ')'
                pass

        elif lastnodetype.startswith('BUILD_SET'):
            self.write('{'); endchar = '}'
        elif lastnodetype.startswith('BUILD_MAP_UNPACK'):
            self.write('{*'); endchar = '}'
        elif lastnodetype.startswith('ROT_TWO'):
            self.write('('); endchar = ')'
        else:
            raise TypeError('Internal Error: n_build_list expects list, tuple, set, or unpack')

        flat_elems = flatten_list(node)

        self.indent_more(INDENT_PER_LEVEL)
        sep = ''
        for elem in flat_elems:
            if elem in ('ROT_THREE', 'EXTENDED_ARG'):
                continue
            assert elem == 'expr'
            line_number = self.line_number
            value = self.traverse(elem)
            if line_number != self.line_number:
                sep += '\n' + self.indent + INDENT_PER_LEVEL[:-1]
            else:
                if sep != '': sep += ' '
            if not last_was_star:
                if have_star:
                    sep += '*'
                    pass
                pass
            else:
                last_was_star = False
            self.write(sep, value)
            sep = ','
        if lastnode.attr == 1 and lastnodetype.startswith('BUILD_TUPLE'):
            self.write(',')
        self.write(endchar)
        self.indent_less(INDENT_PER_LEVEL)

        self.prec = p
        self.prune()
        return

    n_set = n_tuple = n_build_set = n_list

    def n_unpack(self, node):
        if node[0].kind.startswith('UNPACK_EX'):
            # Python 3+
            before_count, after_count = node[0].attr
            for i in range(before_count+1):
                self.preorder(node[i])
                if i != 0:
                    self.write(', ')
            self.write('*')
            for i in range(1, after_count+2):
                self.preorder(node[before_count+i])
                if i != after_count + 1:
                    self.write(', ')
            self.prune()
            return
        for n in node[1:]:
            if n[0].kind == 'unpack':
                n[0].kind = 'unpack_w_parens'
        self.default(node)

    n_unpack_w_parens = n_unpack

    def n_attribute(self, node):
        if (node[0] == 'LOAD_CONST' or
            node[0] == 'expr' and node[0][0] == 'LOAD_CONST'):
            # FIXME: I didn't record which constants parenthesis is
            # necessary. However, I suspect that we could further
            # refine this by looking at operator precedence and
            # eval'ing the constant value (pattr) and comparing with
            # the type of the constant.
            node.kind = 'attribute_w_parens'
        self.default(node)

    def n_assign(self, node):
        # A horrible hack for Python 3.0 .. 3.2
        if 3.0 <= self.version <= 3.2 and len(node) == 2:
            if (node[0][0] == 'LOAD_FAST' and node[0][0].pattr == '__locals__' and
                node[1][0].kind == 'STORE_LOCALS'):
                self.prune()
        self.default(node)

    def n_assign2(self, node):
        for n in node[-2:]:
            if n[0] == 'unpack':
                n[0].kind = 'unpack_w_parens'
        self.default(node)

    def n_assign3(self, node):
        for n in node[-3:]:
            if n[0] == 'unpack':
                n[0].kind = 'unpack_w_parens'
        self.default(node)

    def n_except_cond2(self, node):
        if node[-2][0] == 'unpack':
            node[-2][0].kind = 'unpack_w_parens'
        self.default(node)

    # except_cond3 is only in Python <= 2.6
    n_except_cond3 = n_except_cond2


    def template_engine(self, entry, startnode):
        """The format template interpetation engine.  See the comment at the
        beginning of this module for the how we interpret format
        specifications such as %c, %C, and so on.
        """

        # print("-----")
        # print(startnode)
        # print(entry[0])
        # print('======')

        fmt = entry[0]
        arg = 1
        i = 0

        m = escape.search(fmt)
        while m:
            i = m.end()
            self.write(m.group('prefix'))

            typ = m.group('type') or '{'
            node = startnode
            if m.group('child'):
                node = node[int(m.group('child'))]

            if   typ == '%':	self.write('%')
            elif typ == '+':
                self.line_number += 1
                self.indent_more()
            elif typ == '-':
                self.line_number += 1
                self.indent_less()
            elif typ == '|':
                self.line_number += 1
                self.write(self.indent)
            # Used mostly on the LHS of an assignment
            # BUILD_TUPLE_n is pretty printed and may take care of other uses.
            elif typ == ',':
                if (node.kind in ('unpack', 'unpack_w_parens') and
                    node[0].attr == 1):
                    self.write(',')
            elif typ == 'c':
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

                arg += 1
            elif typ == 'p':
                p = self.prec
                (index, self.prec) = entry[arg]
                self.preorder(node[index])
                self.prec = p
                arg += 1
            elif typ == 'C':
                low, high, sep = entry[arg]
                remaining = len(node[low:high])
                for subnode in node[low:high]:
                    self.preorder(subnode)
                    remaining -= 1
                    if remaining > 0:
                        self.write(sep)
                        pass
                    pass
                arg += 1
            elif typ == 'D':
                low, high, sep = entry[arg]
                remaining = len(node[low:high])
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
                # This code is only used in fragments
                assert isinstance(entry[arg], tuple)
                arg += 1
            elif typ == 'P':
                p = self.prec
                low, high, sep, self.prec = entry[arg]
                remaining = len(node[low:high])
                # remaining = len(node[low:high])
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

                try:
                    self.write(eval(expr, d, d))
                except:
                    raise
            m = escape.search(fmt, i)
        self.write(fmt[i:])

    def default(self, node):
        mapping = self._get_mapping(node)
        table = mapping[0]
        key = node

        for i in mapping[1:]:
            key = key[i]
            pass

        if key.kind in table:
            self.template_engine(table[key.kind], node)
            self.prune()

    def customize(self, customize):
        """
        Special handling for opcodes, such as those that take a variable number
        of arguments -- we add a new entry for each in TABLE_R.
        """
        for k, v in list(customize.items()):
            if k in TABLE_R:
                continue
            op = k[ :k.rfind('_') ]

            if k.startswith('CALL_METHOD'):
                # This happens in PyPy only
                TABLE_R[k] = ('%c(%P)', 0, (1, -1, ', ', 100))
            elif self.version >= 3.6 and k.startswith('CALL_FUNCTION_KW'):
                TABLE_R[k] = ('%c(%P)', 0, (1, -1, ', ', 100))
            elif op == 'CALL_FUNCTION':
                TABLE_R[k] = ('%c(%P)', 0, (1, -1, ', ', 100))
            elif op in ('CALL_FUNCTION_VAR',
                        'CALL_FUNCTION_VAR_KW', 'CALL_FUNCTION_KW'):

                # FIXME: handle everything in customize.
                # Right now, some of this is here, and some in that.

                if v == 0:
                    str = '%c(%C' # '%C' is a dummy here ...
                    p2 = (0, 0, None) # .. because of the None in this
                else:
                    str = '%c(%C, '
                    p2 = (1, -2, ', ')
                if op == 'CALL_FUNCTION_VAR':
                    # Python 3.5 only puts optional args (the VAR part)
                    # lowest down the stack
                    if self.version == 3.5:
                        if str == '%c(%C, ':
                            entry = ('%c(*%C, %c)', 0, p2, -2)
                        elif str == '%c(%C':
                            entry = ('%c(*%C)', 0, (1, 100, ''))
                    elif self.version == 3.4:
                        # CALL_FUNCTION_VAR's top element of the stack contains
                        # the variable argument list
                        if v == 0:
                            str = '%c(*%c)'
                            entry = (str, 0, -2)
                        else:
                            str = '%c(%C, *%c)'
                            entry = (str, 0, p2, -2)
                    else:
                        str += '*%c)'
                        entry = (str, 0, p2, -2)
                elif op == 'CALL_FUNCTION_KW':
                    str += '**%c)'
                    entry = (str, 0, p2, -2)
                elif op == 'CALL_FUNCTION_VAR_KW':
                    str += '*%c, **%c)'
                    # Python 3.5 only puts optional args (the VAR part)
                    # lowest down the stack
                    na = (v & 0xff)  # positional parameters
                    if self.version == 3.5 and na == 0:
                        if p2[2]: p2 = (2, -2, ', ')
                        entry = (str, 0, p2, 1, -2)
                    else:
                        if p2[2]: p2 = (1, -3, ', ')
                        entry = (str, 0, p2, -3, -2)
                    pass
                else:
                    assert False, "Unhandled CALL_FUNCTION %s" % op

                TABLE_R[k] = entry
                pass
            # handled by n_dict:
            # if op == 'BUILD_SLICE':	TABLE_R[k] = ('%C'    ,    (0,-1,':'))
            # handled by n_list:
            # if   op == 'BUILD_LIST':	TABLE_R[k] = ('[%C]'  ,    (0,-1,', '))
            # elif op == 'BUILD_TUPLE':	TABLE_R[k] = ('(%C%,)',    (0,-1,', '))
            pass
        return

    def get_tuple_parameter(self, ast, name):
        """
        If the name of the formal parameter starts with dot,
        it's a tuple parameter, like this:
        #          def MyFunc(xx, (a,b,c), yy):
        #                  print a, b*2, c*42
        In byte-code, the whole tuple is assigned to parameter '.1' and
        then the tuple gets unpacked to 'a', 'b' and 'c'.

        Since identifiers starting with a dot are illegal in Python,
        we can search for the byte-code equivalent to '(a,b,c) = .1'
        """

        assert ast == 'stmts'
        for i in range(len(ast)):
            # search for an assign-statement
            assert ast[i][0] == 'stmt'
            node = ast[i][0][0]
            if (node == 'assign'
                and node[0] == ASSIGN_TUPLE_PARAM(name)):
                # okay, this assigns '.n' to something
                del ast[i]
                # walk lhs; this
                # returns a tuple of identifiers as used
                # within the function definition
                assert node[1] == 'store'
                # if lhs is not a UNPACK_TUPLE (or equiv.),
                # add parenteses to make this a tuple
                # if node[1][0] not in ('unpack', 'unpack_list'):
                return '(' + self.traverse(node[1]) + ')'
            # return self.traverse(node[1])
        raise Exception("Can't find tuple parameter " + name)

    def build_class(self, code):
        """Dump class definition, doc string and class body."""

        assert iscode(code)
        self.classes.append(self.currentclass)
        code = Code(code, self.scanner, self.currentclass)

        indent = self.indent
        # self.println(indent, '#flags:\t', int(code.co_flags))
        ast = self.build_ast(code._tokens, code._customize)
        code._tokens = None # save memory
        assert ast == 'stmts'

        first_stmt = ast[0][0]
        if 3.0 <= self.version <= 3.3:
            try:
                if first_stmt[0] == 'store_locals':
                    if self.hide_internal:
                        del ast[0]
                        first_stmt = ast[0][0]
            except:
                pass

        try:
            if first_stmt == NAME_MODULE:
                if self.hide_internal:
                    del ast[0]
                    first_stmt = ast[0][0]
            pass
        except:
            pass

        have_qualname = False
        if self.version < 3.0:
            # Should we ditch this in favor of the "else" case?
            qualname = '.'.join(self.classes)
            QUAL_NAME = SyntaxTree('stmt',
                            [ SyntaxTree('assign',
                                  [ SyntaxTree('expr', [Token('LOAD_CONST', pattr=qualname)]),
                                    SyntaxTree('store', [ Token('STORE_NAME', pattr='__qualname__')])
                                  ])])
            have_qualname = (ast[0][0] == QUAL_NAME)
        else:
            # Python 3.4+ has constants like 'cmp_to_key.<locals>.K'
            # which are not simple classes like the < 3 case.
            try:
                if (first_stmt[0] == 'assign' and
                    first_stmt[0][0][0] == 'LOAD_CONST' and
                    first_stmt[0][1] == 'store' and
                    first_stmt[0][1][0] == Token('STORE_NAME', pattr='__qualname__')):
                    have_qualname = True
            except:
                pass

        if have_qualname:
            if self.hide_internal: del ast[0]
            pass

        # if docstring exists, dump it
        if (code.co_consts and code.co_consts[0] is not None and len(ast) > 0):
            do_doc = False
            if is_docstring(ast[0]):
                i = 0
                do_doc = True
            elif (len(ast) > 1 and is_docstring(ast[1])):
                i = 1
                do_doc = True
            if do_doc and self.hide_internal:
                try:
                    docstring = ast[i][0][0][0][0].pattr
                except:
                    docstring = code.co_consts[0]
                if print_docstring(self, indent, docstring):
                    self.println()
                    del ast[i]

        # the function defining a class normally returns locals(); we
        # don't want this to show up in the source, thus remove the node
        if len(ast) > 0 and ast[-1][0] == RETURN_LOCALS:
            if self.hide_internal: del ast[-1] # remove last node
        # else:
        #    print ast[-1][-1]

        globals, nonlocals = find_globals_and_nonlocals(ast, set(), set(),
                                                        code, self.version)
        # Add "global" declaration statements at the top
        # of the function
        for g in sorted(globals):
            self.println(indent, 'global ', g)

        for nl in sorted(nonlocals):
            self.println(indent, 'nonlocal ', nl)

        old_name = self.name
        self.gen_source(ast, code.co_name, code._customize)
        self.name = old_name
        code._tokens = None; code._customize = None # save memory
        self.classes.pop(-1)

    def gen_source(self, ast, name, customize, is_lambda=False, returnNone=False):
        """convert SyntaxTree to Python source code"""

        rn = self.return_none
        self.return_none = returnNone
        old_name = self.name
        self.name = name
        # if code would be empty, append 'pass'
        if len(ast) == 0:
            self.println(self.indent, 'pass')
        else:
            self.customize(customize)
            if is_lambda:
                self.write(self.traverse(ast, is_lambda=is_lambda))
            else:
                self.text = self.traverse(ast, is_lambda=is_lambda)
                self.println(self.text)
        self.name = old_name
        self.return_none = rn

    def build_ast(self, tokens, customize, is_lambda=False,
                  noneInNames=False, isTopLevel=False):

        # FIXME: DRY with fragments.py

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
            except (python_parser.ParserError, AssertionError) as e:
                raise ParserError(e, tokens)
            maybe_show_tree(self, ast)
            return ast

        # The bytecode for the end of the main routine has a
        # "return None". However you can't issue a "return" statement in
        # main. So as the old cigarette slogan goes: I'd rather switch (the token stream)
        # than fight (with the grammar to not emit "return None").
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

        # Build a parse tree from a tokenized and massaged disassembly.
        try:
            # FIXME: have p.insts update in a better way
            # modularity is broken here
            p_insts = self.p.insts
            self.p.insts = self.scanner.insts
            ast = python_parser.parse(self.p, tokens, customize)
            self.p.insts = p_insts
        except (python_parser.ParserError, AssertionError) as e:
            raise ParserError(e, tokens)

        maybe_show_tree(self, ast)

        checker(ast, False, self.ast_errors)

        return ast

    @classmethod
    def _get_mapping(cls, node):
        return MAP.get(node, MAP_DIRECT)


#
DEFAULT_DEBUG_OPTS = {
    'asm': False,
    'tree': False,
    'grammar': False
}

# This interface is deprecated. Use simpler code_deparse.
def deparse_code(version, co, out=sys.stdout, showasm=None, showast=False,
                 showgrammar=False, code_objects={}, compile_mode='exec',
                 is_pypy=IS_PYPY, walker=SourceWalker):
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

def code_deparse(co, out=sys.stdout, version=None, debug_opts=DEFAULT_DEBUG_OPTS,
                 code_objects={}, compile_mode='exec', is_pypy=IS_PYPY, walker=SourceWalker):
    """
    ingests and deparses a given code block 'co'. If version is None,
    we will use the current Python interpreter version.
    """

    assert iscode(co)

    if version is None:
        version = float(sys.version[0:3])

    # store final output stream for case of error
    scanner = get_scanner(version, is_pypy=is_pypy)

    tokens, customize = scanner.ingest(co, code_objects=code_objects,
                                       show_asm=debug_opts['asm'])

    debug_parser = dict(PARSER_DEFAULT_DEBUG)
    if debug_opts.get('grammar', None):
        debug_parser['reduce'] = debug_opts['grammar']
        debug_parser['errorstack'] = 'full'

    #  Build Syntax Tree from disassembly.
    linestarts = dict(scanner.opc.findlinestarts(co))
    deparsed = walker(version, out, scanner, showast=debug_opts.get('ast', None),
                      debug_parser=debug_parser, compile_mode=compile_mode,
                      is_pypy=is_pypy, linestarts=linestarts)

    isTopLevel = co.co_name == '<module>'
    deparsed.ast = deparsed.build_ast(tokens, customize, isTopLevel=isTopLevel)

    #### XXX workaround for profiling
    if deparsed.ast is None:
        return None

    assert deparsed.ast == 'stmts', 'Should have parsed grammar start'

    # save memory
    del tokens

    deparsed.mod_globs, nonlocals = find_globals_and_nonlocals(deparsed.ast,
                                                               set(), set(),
                                                               co, version)

    assert not nonlocals

    # convert leading '__doc__ = "..." into doc string
    try:
        if deparsed.ast[0][0] == ASSIGN_DOC_STRING(co.co_consts[0]):
            print_docstring(deparsed, '', co.co_consts[0])
            del deparsed.ast[0]
        if deparsed.ast[-1] == RETURN_NONE:
            deparsed.ast.pop() # remove last node
            # todo: if empty, add 'pass'
    except:
        pass

    deparsed.FUTURE_UNICODE_LITERALS = (
        COMPILER_FLAG_BIT['FUTURE_UNICODE_LITERALS'] & co.co_flags != 0)

    # What we've been waiting for: Generate source from Syntax Tree!
    deparsed.gen_source(deparsed.ast, co.co_name, customize)

    for g in sorted(deparsed.mod_globs):
        deparsed.write('# global %s ## Warning: Unused global\n' % g)

    if deparsed.ast_errors:
        deparsed.write("# NOTE: have internal decompilation grammar errors.\n")
        deparsed.write("# Use -t option to show full context.")
        for err in deparsed.ast_errors:
            deparsed.write(err)
        raise SourceWalkerError("Deparsing hit an internal grammar-rule bug")

    if deparsed.ERROR:
        raise SourceWalkerError("Deparsing stopped due to parse error")
    return deparsed

def deparse_code2str(code, out=sys.stdout, version=None,
                     debug_opts=DEFAULT_DEBUG_OPTS,
                     code_objects={}, compile_mode='exec',
                     is_pypy=IS_PYPY, walker=SourceWalker):
    """Return the deparsed text for a Python code object. `out` is where any intermediate
    output for assembly or tree output will be sent.
    """
    return deparse_code(version, code, out, showasm=debug_opts.get('asm', None),
                        showast=debug_opts.get('tree', None),
                        showgrammar=debug_opts.get('grammar', None), code_objects=code_objects,
                        compile_mode=compile_mode, is_pypy=is_pypy, walker=walker).text

if __name__ == '__main__':
    def deparse_test(co):
        "This is a docstring"
        s = deparse_code2str(co, debug_opts={'asm':'after', 'tree':True})
        # s = deparse_code2str(co, showasm=None, showast=False,
        #                       showgrammar=True)
        print(s)
        return
    deparse_test(deparse_test.__code__)
