#  Copyright (c) 2015-2022 by Rocky Bernstein
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

# The below is a bit long, but still it is somewhat abbreviated.
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
# either tables MAP_R, or MAP_DIRECT where the key is the
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
#          N&K               N
#         / | ... \        / | ... \
#        O  O      O      O  O      K
#
#
#      TABLE_DIRECT      TABLE_R
#
#   The default table is TABLE_DIRECT mapping By far, most rules used work this way.
#
#   The key K is then extracted from the subtree and used to find one
#   of the tables, T listed above.  The result after applying T[K] is
#   a format string and arguments (a la printf()) for the formatting
#   engine.
#
#   Escapes in the format string are:
#
#     %c  evaluate/traverse the node recursively. Its argument is a single
#         integer or tuple representing a node index.
#         If a tuple is given, the first item is the node index while
#         the second item is a string giving the node/noterminal name.
#         This name will be checked at runtime against the node type.
#
#     %p  like %c but sets the operator precedence.
#         Its argument then is a tuple indicating the node
#         index and the precedence value, an integer. If 3 items are given,
#         the second item is the nonterminal name and the precedence is given last.
#
#     %C  evaluate/travers children recursively, with sibling children separated by the
#         given string.  It needs a 3-tuple: a starting node, the maximimum
#         value of an end node, and a string to be inserted between sibling children
#
#     %,  Append ',' if last %C only printed one item. This is mostly for tuples
#         on the LHS of an assignment statement since BUILD_TUPLE_n pretty-prints
#         other tuples. The specifier takes no arguments
#
#     %P  same as %C but sets operator precedence.  Its argument is a 4-tuple:
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
#     %{EXPR} Python eval(EXPR) in context of node. Takes no arguments
#
#     %[N]{EXPR} Python eval(EXPR) in context of node[N]. Takes no arguments
#
#     %[N]{%X} evaluate/recurse on child node[N], using specifier %X.
#     %X can be one of the above, e.g. %c, %p, etc. Takes the arguemnts
#     that the specifier uses.
#
#     %% literal '%'. Takes no arguments.
#
#
#   The '%' may optionally be followed by a number (C) in square
#   brackets, which makes the template_engine walk down to N[C] before
#   evaluating the escape code.

import sys

IS_PYPY = "__pypy__" in sys.builtin_module_names

from spark_parser import GenericASTTraversal
from xdis import COMPILER_FLAG_BIT, iscode
from xdis.version_info import PYTHON_VERSION_TRIPLE

import uncompyle6.parser as python_parser
from uncompyle6.parser import get_python_parser
from uncompyle6.parsers.treenode import SyntaxTree
from uncompyle6.scanner import Code, get_scanner
from uncompyle6.scanners.tok import Token
from uncompyle6.semantics.check_ast import checker
from uncompyle6.semantics.consts import (ASSIGN_DOC_STRING, ASSIGN_TUPLE_PARAM,
                                         INDENT_PER_LEVEL, LINE_LENGTH, MAP,
                                         MAP_DIRECT, NAME_MODULE, NONE, PASS,
                                         PRECEDENCE, RETURN_LOCALS,
                                         RETURN_NONE, TAB, TABLE_R, escape)
from uncompyle6.semantics.customize import customize_for_version
from uncompyle6.semantics.gencomp import ComprehensionMixin
from uncompyle6.semantics.helper import (
    find_globals_and_nonlocals,
    print_docstring
)
from uncompyle6.semantics.make_function1 import make_function1
from uncompyle6.semantics.make_function2 import make_function2
from uncompyle6.semantics.make_function3 import make_function3
from uncompyle6.semantics.make_function36 import make_function36
from uncompyle6.semantics.n_actions import NonterminalActions
from uncompyle6.semantics.parser_error import ParserError
from uncompyle6.semantics.transform import TreeTransform, is_docstring
from uncompyle6.show import maybe_show_tree
from uncompyle6.util import better_repr
if PYTHON_VERSION_TRIPLE < (2, 5):
    from cStringIO import StringIO
else:
    from StringIO import StringIO

DEFAULT_DEBUG_OPTS = {"asm": False, "tree": False, "grammar": False}

def unicode(x): return x

PARSER_DEFAULT_DEBUG = {
    "rules": False,
    "transition": False,
    "reduce": False,
    "errorstack": "full",
    "context": True,
    "dups": False,
}

PARSER_DEFAULT_DEBUG = {
    "rules": False,
    "transition": False,
    "reduce": False,
    "errorstack": "full",
    "context": True,
    "dups": False,
}

TREE_DEFAULT_DEBUG = {"before": False, "after": False}

DEFAULT_DEBUG_OPTS = {
    "asm": False,
    "tree": TREE_DEFAULT_DEBUG,
    "grammar": dict(PARSER_DEFAULT_DEBUG),
}


class SourceWalkerError(Exception):
    def __init__(self, errmsg):
        self.errmsg = errmsg

    def __str__(self):
        return self.errmsg


class SourceWalker(GenericASTTraversal, NonterminalActions, ComprehensionMixin):
    stacked_params = ("f", "indent", "is_lambda", "_globals")

    def __init__(
        self,
        version,
        out,
        scanner,
        showast=TREE_DEFAULT_DEBUG,
        debug_parser=PARSER_DEFAULT_DEBUG,
        compile_mode="exec",
        is_pypy=IS_PYPY,
        linestarts={},
        tolerate_errors=False,
    ):
        """`version' is the Python version (a float) of the Python dialect
        of both the syntax tree and language we should produce.

        `out' is IO-like file pointer to where the output should go. It
        whould have a getvalue() method.

        `scanner' is a method to call when we need to scan tokens. Sometimes
        in producing output we will run across further tokens that need
        to be scaned.

        If `showast' is True, we print the syntax tree.

        `compile_mode' is is either 'exec' or 'single'. It is the compile
        mode that was used to create the Syntax Tree and specifies a
        gramar variant within a Python version to use.

        `is_pypy` should be True if the Syntax Tree was generated for PyPy.

        `linestarts` is a dictionary of line number to bytecode offset. This
        can sometimes assist in determinte which kind of source-code construct
        to use when there is ambiguity.

        """
        GenericASTTraversal.__init__(self, ast=None)

        self.scanner = scanner
        params = {"f": out, "indent": ""}
        self.version = version
        self.p = get_python_parser(
            version,
            debug_parser=dict(debug_parser),
            compile_mode=compile_mode,
            is_pypy=is_pypy,
        )

        # Initialize p_lambda on demand
        self.p_lambda = None

        self.treeTransform = TreeTransform(version=self.version, show_ast=showast)
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
        self.insts = scanner.insts
        self.offset2inst_index = scanner.offset2inst_index

        # This is in Python 2.6 on. It changes the way
        # strings get interpreted. See n_LOAD_CONST
        self.FUTURE_UNICODE_LITERALS = False

        # Sometimes we may want to continue decompiling when there are errors
        # and sometimes not
        self.tolerate_errors = tolerate_errors

        # If we are in a 3.6+ format string, we may need an
        # extra level of parens when seeing a lambda. We also use
        # this to understand whether or not to add the "f" prefix.
        # When not "None" it is a string of the last nonterminal
        # that started the format string
        self.in_format_string = None

        # hide_internal suppresses displaying the additional instructions that sometimes
        # exist in code but but were not written in the source code.
        # An example is:
        # __module__ = __name__
        self.hide_internal = True
        self.compile_mode = compile_mode
        self.name = None
        self.version = version
        self.is_pypy = is_pypy
        customize_for_version(self, is_pypy, version)
        return

    def maybe_show_tree(self, ast, phase):
        if self.showast.get("before", False):
            self.println(
                """
---- end before transform
"""
            )
        if self.showast.get("after", False):
            self.println(
                """
---- begin after transform
"""
                + " "
            )
        if self.showast.get(phase, False):
            maybe_show_tree(self, ast)

    def str_with_template(self, ast):
        stream = sys.stdout
        stream.write(self.str_with_template1(ast, "", None))
        stream.write("\n")

    def str_with_template1(self, ast, indent, sibNum=None):
        rv = str(ast.kind)

        if sibNum is not None:
            rv = "%2d. %s" % (sibNum, rv)
        enumerate_children = False
        if len(ast) > 1:
            rv += " (%d)" % (len(ast))
            enumerate_children = True

        if ast in PRECEDENCE:
            rv += ", precedence %s" % PRECEDENCE[ast]

        mapping = self._get_mapping(ast)
        table = mapping[0]
        key = ast
        for i in mapping[1:]:
            key = key[i]
            pass

        if ast.transformed_by is not None:
            if ast.transformed_by is True:
                rv += " transformed"
            else:
                rv += " transformed by %s" % ast.transformed_by
                pass
            pass
        if key.kind in table:
            rv += ": %s" % str(table[key.kind])

        rv = indent + rv
        indent += "    "
        i = 0
        for node in ast:

            if hasattr(node, "__repr1__"):
                if enumerate_children:
                    child = self.str_with_template1(node, indent, i)
                else:
                    child = self.str_with_template1(node, indent, None)
            else:
                inst = node.format(line_prefix="L.")
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
        if line_number != self.line_number:
            self.write("\n" + self.indent + INDENT_PER_LEVEL[:-1])
        return self.line_number

    f = property(
        lambda s: s.params["f"],
        lambda s, x: s.params.__setitem__("f", x),
        lambda s: s.params.__delitem__("f"),
        None,
    )

    indent = property(
        lambda s: s.params["indent"],
        lambda s, x: s.params.__setitem__("indent", x),
        lambda s: s.params.__delitem__("indent"),
        None,
    )

    is_lambda = property(
        lambda s: s.params["is_lambda"],
        lambda s, x: s.params.__setitem__("is_lambda", x),
        lambda s: s.params.__delitem__("is_lambda"),
        None,
    )

    _globals = property(
        lambda s: s.params["_globals"],
        lambda s, x: s.params.__setitem__("_globals", x),
        lambda s: s.params.__delitem__("_globals"),
        None,
    )

    def set_pos_info(self, node):
        if hasattr(node, "linestart") and node.linestart:
            self.line_number = node.linestart

    def preorder(self, node=None):
        super(SourceWalker, self).preorder(node)
        self.set_pos_info(node)

    def indent_more(self, indent=TAB):
        self.indent += indent

    def indent_less(self, indent=TAB):
        self.indent = self.indent[: -len(indent)]

    def traverse(self, node, indent=None, is_lambda=False):
        self.param_stack.append(self.params)
        if indent is None:
            indent = self.indent
        p = self.pending_newlines
        self.pending_newlines = 0
        self.params = {
            "_globals": {},
            "_nonlocals": {},  # Python 3 has nonlocal
            "f": StringIO(),
            "indent": indent,
            "is_lambda": is_lambda,
        }
        self.preorder(node)
        self.f.write("\n" * self.pending_newlines)
        result = self.f.getvalue()
        self.params = self.param_stack.pop()
        self.pending_newlines = p
        return result

    def write(self, *data):
        if (len(data) == 0) or (len(data) == 1 and data[0] == ""):
            return
        out = "".join((str(j) for j in data))
        n = 0
        for i in out:
            if i == "\n":
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
            self.f.write("\n" * self.pending_newlines)
            self.pending_newlines = 0

        for i in out[::-1]:
            if i == "\n":
                self.pending_newlines += 1
            else:
                break

        if self.pending_newlines:
            out = out[: -self.pending_newlines]
        self.f.write(out)

    def println(self, *data):
        if data and not (len(data) == 1 and data[0] == ""):
            self.write(*data)
        self.pending_newlines = max(self.pending_newlines, 1)

    def is_return_none(self, node):
        # Is there a better way?
        ret = (
            node[0] == "return_expr"
            and node[0][0] == "expr"
            and node[0][0][0] == "LOAD_CONST"
            and node[0][0][0].pattr is None
        )
        if self.version <= (2, 6):
            return ret
        else:
            # FIXME: should the SyntaxTree expression be folded into
            # the global RETURN_NONE constant?
            return ret or node == SyntaxTree(
                "return", [SyntaxTree("return_expr", [NONE]), Token("RETURN_VALUE")]
            )

    def pp_tuple(self, tup):
        """Pretty print a tuple"""
        last_line = self.f.getvalue().split("\n")[-1]
        l = len(last_line) + 1
        indent = " " * l
        self.write("(")
        sep = ""
        for item in tup:
            self.write(sep)
            l += len(sep)
            s = better_repr(item, self.version)
            l += len(s)
            self.write(s)
            sep = ","
            if l > LINE_LENGTH:
                l = 0
                sep += "\n" + indent
            else:
                sep += " "
                pass
            pass
        if len(tup) == 1:
            self.write(", ")
        self.write(")")

    # Python changes make function this much that we need at least 3 different routines,
    # and probably more in the future.
    def make_function(self, node, is_lambda, nested=1, code_node=None, annotate=None):
        if self.version <= (1, 2):
            make_function1(self, node, is_lambda, nested, code_node)
        elif self.version <= (2, 7):
            make_function2(self, node, is_lambda, nested, code_node)
        elif (3, 0) <= self.version < (3, 6):
            make_function3(self, node, is_lambda, nested, code_node)
        elif self.version >= (3, 6):
            make_function36(self, node, is_lambda, nested, code_node)

    def print_super_classes(self, node):
        if not (node == "tuple"):
            return

        n_subclasses = len(node[:-1])
        if n_subclasses > 0 or self.version > (2, 4):
            # Not an old-style pre-2.2 class
            self.write("(")

        line_separator = ", "
        sep = ""
        for elem in node[:-1]:
            value = self.traverse(elem)
            self.write(sep, value)
            sep = line_separator

        if n_subclasses > 0 or self.version > (2, 4):
            # Not an old-style pre-2.2 class
            self.write(")")

    def print_super_classes3(self, node):
        n = len(node) - 1
        if node.kind != "expr":
            if node == "kwarg":
                self.template_engine(("(%[0]{attr}=%c)", 1), node)
                return

            kwargs = None
            assert node[n].kind.startswith("CALL_FUNCTION")

            if node[n].kind.startswith("CALL_FUNCTION_KW"):
                if self.is_pypy:
                    # FIXME: this doesn't handle positional and keyword args
                    # properly. Need to do something more like that below
                    # in the non-PYPY 3.6 case.
                    self.template_engine(("(%[0]{attr}=%c)", 1), node[n - 1])
                    return
                else:
                    kwargs = node[n - 1].attr

                assert isinstance(kwargs, tuple)
                i = n - (len(kwargs) + 1)
                j = 1 + n - node[n].attr
            else:
                i = start = n - 2
                for i in range(start, 0, -1):
                    if not node[i].kind in ["expr", "call", "LOAD_CLASSNAME"]:
                        break
                    pass

                if i == start:
                    return
                i += 2

            line_separator = ", "
            sep = ""
            self.write("(")
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
            if node[0] == "LOAD_STR":
                return
            value = self.traverse(node[0])
            self.write("(")
            self.write(value)
            pass

        self.write(")")

    def kv_map(self, kv_node, sep, line_number, indent):
        first_time = True
        for kv in kv_node:
            assert kv in ("kv", "kv2", "kv3")

            # kv ::= DUP_TOP expr ROT_TWO expr STORE_SUBSCR
            # kv2 ::= DUP_TOP expr expr ROT_THREE STORE_SUBSCR
            # kv3 ::= expr expr STORE_MAP

            # FIXME: DRY this and the above
            if kv == "kv":
                self.write(sep)
                name = self.traverse(kv[-2], indent="")
                if first_time:
                    line_number = self.indent_if_source_nl(line_number, indent)
                    first_time = False
                    pass
                line_number = self.line_number
                self.write(name, ": ")
                value = self.traverse(kv[1], indent=self.indent + (len(name) + 2) * " ")
            elif kv == "kv2":
                self.write(sep)
                name = self.traverse(kv[1], indent="")
                if first_time:
                    line_number = self.indent_if_source_nl(line_number, indent)
                    first_time = False
                    pass
                line_number = self.line_number
                self.write(name, ": ")
                value = self.traverse(
                    kv[-3], indent=self.indent + (len(name) + 2) * " "
                )
            elif kv == "kv3":
                self.write(sep)
                name = self.traverse(kv[-2], indent="")
                if first_time:
                    line_number = self.indent_if_source_nl(line_number, indent)
                    first_time = False
                    pass
                line_number = self.line_number
                self.write(name, ": ")
                line_number = self.line_number
                value = self.traverse(kv[0], indent=self.indent + (len(name) + 2) * " ")
                pass
            self.write(value)
            sep = ", "
            if line_number != self.line_number:
                sep += "\n" + self.indent + "  "
                line_number = self.line_number
                pass
            pass

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
            self.write(m.group("prefix"))

            typ = m.group("type") or "{"
            node = startnode
            if m.group("child"):
                node = node[int(m.group("child"))]

            if typ == "%":
                self.write("%")
            elif typ == "+":
                self.line_number += 1
                self.indent_more()
            elif typ == "-":
                self.line_number += 1
                self.indent_less()
            elif typ == "|":
                self.line_number += 1
                self.write(self.indent)
            # Used mostly on the LHS of an assignment
            # BUILD_TUPLE_n is pretty printed and may take care of other uses.
            elif typ == ",":
                if node.kind in ("unpack", "unpack_w_parens") and node[0].attr == 1:
                    self.write(",")
            elif typ == "c":
                index = entry[arg]
                if isinstance(index, tuple):
                    if isinstance(index[1], str):
                        # if node[index[0]] != index[1]:
                        #     from trepan.api import debug; debug()
                        assert node[index[0]] == index[1], (
                            "at %s[%d], expected '%s' node; got '%s'"
                            % (node.kind, arg, index[1], node[index[0]].kind,)
                        )
                    else:
                        assert node[index[0]] in index[1], (
                            "at %s[%d], expected to be in '%s' node; got '%s'"
                            % (node.kind, arg, index[1], node[index[0]].kind,)
                        )

                    index = index[0]
                assert isinstance(index, int), (
                    "at %s[%d], %s should be int or tuple"
                    % (node.kind, arg, type(index),)
                )

                try:
                    node[index]
                except IndexError:
                    raise RuntimeError(
                        """
                        Expanding '%s' in template '%s[%s]':
                        %s is invalid; has only %d entries
                        """ % (node.kind, entry, arg, index, len(node))
                    )
                self.preorder(node[index])

                arg += 1
            elif typ == "p":
                p = self.prec
                # entry[arg]
                tup = entry[arg]
                assert isinstance(tup, tuple)
                if len(tup) == 3:
                    (index, nonterm_name, self.prec) = tup
                    if isinstance(tup[1], str):
                        assert node[index] == nonterm_name, (
                            "at %s[%d], expected '%s' node; got '%s'"
                            % (node.kind, arg, nonterm_name, node[index].kind,)
                        )
                    else:
                        assert node[tup[0]] in tup[1], (
                            "at %s[%d], expected to be in '%s' node; got '%s'"
                            % (node.kind, arg, index[1], node[index[0]].kind,)
                        )

                else:
                    assert len(tup) == 2
                    (index, self.prec) = entry[arg]

                self.preorder(node[index])
                self.prec = p
                arg += 1
            elif typ == "C":
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
            elif typ == "D":
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
            elif typ == "x":
                # This code is only used in fragments
                assert isinstance(entry[arg], tuple)
                arg += 1
            elif typ == "P":
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
            elif typ == "{":
                expr = m.group("expr")

                # Line mapping stuff
                if (
                    hasattr(node, "linestart")
                    and node.linestart
                    and hasattr(node, "current_line_number")
                ):
                    self.source_linemap[self.current_line_number] = node.linestart

                if expr[0] == "%":
                    index = entry[arg]
                    self.template_engine((expr, index), node)
                    arg += 1
                else:
                    d = node.__dict__
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
            op = k[: k.rfind("_")]

            if k.startswith("CALL_METHOD"):
                # This happens in PyPy and Python 3.7+
                TABLE_R[k] = ("%c(%P)", (0, "expr"), (1, -1, ", ", 100))
            elif self.version >= (3, 6) and k.startswith("CALL_FUNCTION_KW"):
                TABLE_R[k] = ("%c(%P)", (0, "expr"), (1, -1, ", ", 100))
            elif op == "CALL_FUNCTION":
                TABLE_R[k] = (
                    "%c(%P)",
                    (0, "expr"),
                    (1, -1, ", ", PRECEDENCE["yield"] - 1),
                )
            elif op in (
                "CALL_FUNCTION_VAR",
                "CALL_FUNCTION_VAR_KW",
                "CALL_FUNCTION_KW",
            ):

                # FIXME: handle everything in customize.
                # Right now, some of this is here, and some in that.

                if v == 0:
                    str = "%c(%C"  # '%C' is a dummy here ...
                    p2 = (0, 0, None)  # .. because of the None in this
                else:
                    str = "%c(%C, "
                    p2 = (1, -2, ", ")
                if op == "CALL_FUNCTION_VAR":
                    # Python 3.5 only puts optional args (the VAR part)
                    # the lowest down the stack
                    if self.version == (3, 5):
                        if str == "%c(%C, ":
                            entry = ("%c(*%C, %c)", 0, p2, -2)
                        elif str == "%c(%C":
                            entry = ("%c(*%C)", 0, (1, 100, ""))
                    elif self.version == (3, 4):
                        # CALL_FUNCTION_VAR's top element of the stack contains
                        # the variable argument list
                        if v == 0:
                            str = "%c(*%c)"
                            entry = (str, 0, -2)
                        else:
                            str = "%c(%C, *%c)"
                            entry = (str, 0, p2, -2)
                    else:
                        str += "*%c)"
                        entry = (str, 0, p2, -2)
                elif op == "CALL_FUNCTION_KW":
                    str += "**%c)"
                    entry = (str, 0, p2, -2)
                elif op == "CALL_FUNCTION_VAR_KW":
                    str += "*%c, **%c)"
                    # Python 3.5 only puts optional args (the VAR part)
                    # the lowest down the stack
                    na = v & 0xFF  # positional parameters
                    if self.version == (3, 5) and na == 0:
                        if p2[2]:
                            p2 = (2, -2, ", ")
                        entry = (str, 0, p2, 1, -2)
                    else:
                        if p2[2]:
                            p2 = (1, -3, ", ")
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

    # This code is only for Python 1.x - 2.1 ish!
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

        assert ast == "stmts"
        for i in range(len(ast)):
            # search for an assign-statement
            if ast[i] == "sstmt":
                node = ast[i][0]
            else:
                node = ast[i]
            if node == "assign" and node[0] == ASSIGN_TUPLE_PARAM(name):
                # okay, this assigns '.n' to something
                del ast[i]
                # walk lhs; this
                # returns a tuple of identifiers as used
                # within the function definition
                assert node[1] == "store"
                # if lhs is not a UNPACK_TUPLE (or equiv.),
                # add parenteses to make this a tuple
                # if node[1][0] not in ('unpack', 'unpack_list'):
                result = self.traverse(node[1])
                if not (result.startswith("(") and result.endswith(")")):
                    result = "(%s)" % result
                return result
            # return self.traverse(node[1])
        return "(" + name
        raise Exception("Can't find tuple parameter " + name)

    def build_class(self, code):
        """Dump class definition, doc string and class body."""

        assert iscode(code)
        self.classes.append(self.currentclass)
        code = Code(code, self.scanner, self.currentclass)

        indent = self.indent
        # self.println(indent, '#flags:\t', int(code.co_flags))
        ast = self.build_ast(code._tokens, code._customize, code)

        # save memory by deleting no-longer-used structures
        code._tokens = None

        if ast[0] == "sstmt":
            ast[0] = ast[0][0]
        first_stmt = ast[0]

        if ast[0] == "docstring":
            self.println(self.traverse(ast[0]))
            del ast[0]
            first_stmt = ast[0]

        if (3, 0) <= self.version <= (3, 3):
            try:
                if first_stmt == "store_locals":
                    if self.hide_internal:
                        del ast[0]
                        if ast[0] == "sstmt":
                            ast[0] = ast[0][0]
                        first_stmt = ast[0]
            except:
                pass

        try:
            if first_stmt == NAME_MODULE:
                if self.hide_internal:
                    del ast[0]
                    first_stmt = ast[0]
            pass
        except:
            pass

        have_qualname = False
        if len(ast):
            if ast[0] == "sstmt":
                ast[0] = ast[0][0]
            first_stmt = ast[0]

        if self.version < (3, 0):
            # Should we ditch this in favor of the "else" case?
            qualname = ".".join(self.classes)
            QUAL_NAME = SyntaxTree(
                "assign",
                [
                    SyntaxTree("expr", [Token("LOAD_CONST", pattr=qualname)]),
                    SyntaxTree(
                        "store", [Token("STORE_NAME", pattr="__qualname__")]
                    ),
                ],
            )
            # FIXME: is this right now that we've redone the grammar?
            have_qualname = ast[0] == QUAL_NAME
        else:
            # Python 3.4+ has constants like 'cmp_to_key.<locals>.K'
            # which are not simple classes like the < 3 case.
            try:
                if (
                    first_stmt == "assign"
                    and first_stmt[0][0] == "LOAD_STR"
                    and first_stmt[1] == "store"
                    and first_stmt[1][0] == Token("STORE_NAME", pattr="__qualname__")
                ):
                    have_qualname = True
            except:
                pass

        if have_qualname:
            if self.hide_internal:
                del ast[0]
            pass

        # if docstring exists, dump it
        if code.co_consts and code.co_consts[0] is not None and len(ast) > 0:
            do_doc = False
            if is_docstring(ast[0], self.version, code.co_consts):
                i = 0
                do_doc = True
            elif len(ast) > 1 and is_docstring(ast[1], self.version, code.co_consts):
                i = 1
                do_doc = True
            if do_doc and self.hide_internal:
                try:
                    # FIXME: Is there an extra [0]?
                    docstring = ast[i][0][0][0][0].pattr
                except:
                    docstring = code.co_consts[0]
                if print_docstring(self, indent, docstring):
                    self.println()
                    del ast[i]

        # The function defining a class returns locals() in Python somewhere less than
        # 3.7.
        #
        # We don't want this to show up in the source, so remove the node.
        if len(ast):
            if ast == "stmts" and ast[-1] == "sstmt":
                return_locals_parent = ast[-1]
                parent_index = 0
            else:
                return_locals_parent = ast
                parent_index = -1
            return_locals = return_locals_parent[parent_index]
            if return_locals == RETURN_LOCALS:
                if self.hide_internal:
                    del return_locals_parent[parent_index]
                    pass
                pass
            # else:
            #    print stmt[-1]


        globals, nonlocals = find_globals_and_nonlocals(
            ast, set(), set(), code, self.version
        )
        # Add "global" declaration statements at the top
        # of the function
        for g in sorted(globals):
            self.println(indent, "global ", g)

        for nl in sorted(nonlocals):
            self.println(indent, "nonlocal ", nl)

        old_name = self.name
        self.gen_source(ast, code.co_name, code._customize)
        self.name = old_name

        # save memory by deleting no-longer-used structures
        code._tokens = None
        code._customize = None

        self.classes.pop(-1)

    def gen_source(
        self,
        ast,
        name,
        customize,
        is_lambda=False,
        returnNone=False,
        debug_opts=DEFAULT_DEBUG_OPTS,
    ):
        """convert parse tree to Python source code"""

        rn = self.return_none
        self.return_none = returnNone
        old_name = self.name
        self.name = name
        self.debug_opts = debug_opts
        # if code would be empty, append 'pass'
        if len(ast) == 0:
            self.println(self.indent, "pass")
        else:
            self.customize(customize)
            self.text = self.traverse(ast, is_lambda=is_lambda)
            # In a formatted string using "lambda',  we should not add "\n".
            # For example in:
            #    f'{(lambda x:x)("8")!r}'
            # Adding a "\n" after "lambda x: x" will give an error message:
            #    SyntaxError: f-string expression part cannot include a backslash
            # So avoid \n after writing text
            self.write(self.text)
        self.name = old_name
        self.return_none = rn

    def build_ast(
        self,
        tokens,
        customize,
        code,
        is_lambda=False,
        noneInNames=False,
        is_top_level_module=False,
    ):

        # FIXME: DRY with fragments.py

        # assert isinstance(tokens[0], Token)

        if is_lambda:
            for t in tokens:
                if t.kind == "RETURN_END_IF":
                    t.kind = "RETURN_END_IF_LAMBDA"
                elif t.kind == "RETURN_VALUE":
                    t.kind = "RETURN_VALUE_LAMBDA"
            tokens.append(Token("LAMBDA_MARKER"))
            try:
                # FIXME: have p.insts update in a better way
                # modularity is broken here
                p_insts = self.p.insts
                self.p.insts = self.scanner.insts
                self.p.offset2inst_index = self.scanner.offset2inst_index
                ast = python_parser.parse(self.p, tokens, customize, code)
                self.customize(customize)
                self.p.insts = p_insts
            except python_parser.ParserError, e:
                raise ParserError(e, tokens, self.p.debug["reduce"])
            except AssertionError, e:
                raise ParserError(e, tokens, self.p.debug["reduce"])
            transform_tree = self.treeTransform.transform(ast, code)
            self.maybe_show_tree(ast, phase="after")
            del ast  # Save memory
            return transform_tree

        # The bytecode for the end of the main routine has a
        # "return None". However, you can't issue a "return" statement in
        # main. So as the old cigarette slogan goes: I'd rather switch (the token stream)
        # than fight (with the grammar to not emit "return None").
        if self.hide_internal:
            if len(tokens) >= 2 and not noneInNames:
                if tokens[-1].kind in ("RETURN_VALUE", "RETURN_VALUE_LAMBDA"):
                    # Python 3.4's classes can add a "return None" which is
                    # invalid syntax.
                    if tokens[-2].kind == "LOAD_CONST":
                        if is_top_level_module or tokens[-2].pattr is None:
                            del tokens[-2:]
                        else:
                            tokens.append(Token("RETURN_LAST"))
                    else:
                        tokens.append(Token("RETURN_LAST"))
            if len(tokens) == 0:
                return PASS

        # Build a parse tree from a tokenized and massaged disassembly.
        try:
            # FIXME: have p.insts update in a better way
            # modularity is broken here
            p_insts = self.p.insts
            self.p.insts = self.scanner.insts
            self.p.offset2inst_index = self.scanner.offset2inst_index
            self.p.opc = self.scanner.opc
            ast = python_parser.parse(self.p, tokens, customize, code)
            self.p.insts = p_insts
        except python_parser.ParserError, e:
            raise ParserError(e, tokens, self.p.debug["reduce"])

        checker(ast, False, self.ast_errors)

        self.customize(customize)
        transform_tree = self.treeTransform.transform(ast, code)

        self.maybe_show_tree(ast, phase="before")

        del ast  # Save memory
        return transform_tree

    @classmethod
    def _get_mapping(cls, node):
        return MAP.get(node, MAP_DIRECT)


def code_deparse(
    co,
    out=sys.stdout,
    version=None,
    debug_opts=DEFAULT_DEBUG_OPTS,
    code_objects={},
    compile_mode="exec",
    is_pypy=IS_PYPY,
    walker=SourceWalker,
):
    """
    ingests and deparses a given code block 'co'. If version is None,
    we will use the current Python interpreter version.
    """

    assert iscode(co)

    if version is None:
        version = PYTHON_VERSION_TRIPLE

    # store final output stream for case of error
    scanner = get_scanner(version, is_pypy=is_pypy, show_asm=debug_opts["asm"])

    tokens, customize = scanner.ingest(
        co, code_objects=code_objects, show_asm=debug_opts["asm"]
    )

    debug_parser = debug_opts.get("grammar", dict(PARSER_DEFAULT_DEBUG))

    #  Build Syntax Tree from disassembly.
    linestarts = dict(scanner.opc.findlinestarts(co))
    deparsed = walker(
        version,
        out,
        scanner,
        showast=debug_opts.get("tree", TREE_DEFAULT_DEBUG),
        debug_parser=debug_parser,
        compile_mode=compile_mode,
        is_pypy=is_pypy,
        linestarts=linestarts,
    )

    is_top_level_module = co.co_name == "<module>"
    if compile_mode == "eval":
        deparsed.hide_internal = False
    deparsed.compile_mode = compile_mode
    deparsed.ast = deparsed.build_ast(
        tokens,
        customize,
        co,
        is_lambda=(compile_mode == "lambda"),
        is_top_level_module=is_top_level_module,
    )

    #### XXX workaround for profiling
    if deparsed.ast is None:
        return None

    # FIXME use a lookup table here.
    if compile_mode == "lambda":
        expected_start = "lambda_start"
    elif compile_mode == "eval":
        expected_start = "expr_start"
    elif compile_mode == "expr":
        expected_start = "expr_start"
    elif compile_mode == "exec":
        expected_start = "stmts"
    elif compile_mode == "single":
        # expected_start = "single_start"
        expected_start = None
    else:
        expected_start = None
    if expected_start:
        assert (
            deparsed.ast == expected_start
        ), (
            "Should have parsed grammar start to '%s'; got: %s" %
            (expected_start, deparsed.ast.kind)
            )
    # save memory
    del tokens

    deparsed.mod_globs, nonlocals = find_globals_and_nonlocals(
        deparsed.ast, set(), set(), co, version
    )

    assert not nonlocals

    if version >= (3, 0):
        load_op = "LOAD_STR"
    else:
        load_op = "LOAD_CONST"

    # convert leading '__doc__ = "..." into doc string
    try:
        stmts = deparsed.ast
        first_stmt = stmts[0][0]
        if (version >= (3, 6, 0)):
            if first_stmt[0] == "SETUP_ANNOTATIONS":
                del stmts[0]
                assert stmts[0] == "sstmt"
                # Nuke sstmt
                first_stmt = stmts[0][0]
                pass
            pass
        if first_stmt == ASSIGN_DOC_STRING(co.co_consts[0], load_op):
            print_docstring(deparsed, "", co.co_consts[0])
            del stmts[0]
        if stmts[-1] == RETURN_NONE:
            stmts.pop()  # remove last node
            # todo: if empty, add 'pass'
    except:
        pass

    deparsed.FUTURE_UNICODE_LITERALS = (
        COMPILER_FLAG_BIT["FUTURE_UNICODE_LITERALS"] & co.co_flags != 0
    )

    # What we've been waiting for: Generate source from Syntax Tree!
    deparsed.gen_source(
        deparsed.ast,
        name=co.co_name,
        customize=customize,
        is_lambda=compile_mode == "lambda",
        debug_opts=debug_opts,
    )

    for g in sorted(deparsed.mod_globs):
        deparsed.write("# global %s ## Warning: Unused global\n" % g)

    if deparsed.ast_errors:
        deparsed.write("# NOTE: have internal decompilation grammar errors.\n")
        deparsed.write("# Use -T option to show full context.")
        for err in deparsed.ast_errors:
            deparsed.write(err)
        raise SourceWalkerError("Deparsing hit an internal grammar-rule bug")

    if deparsed.ERROR:
        raise SourceWalkerError("Deparsing stopped due to parse error")
    return deparsed


def deparse_code2str(
    code,
    out=sys.stdout,
    version=None,
    debug_opts=DEFAULT_DEBUG_OPTS,
    code_objects={},
    compile_mode="exec",
    is_pypy=IS_PYPY,
    walker=SourceWalker,
):
    """Return the deparsed text for a Python code object. `out` is where any intermediate
    output for assembly or tree output will be sent.
    """
    return code_deparse(
        code,
        out,
        version,
        debug_opts,
        code_objects=code_objects,
        compile_mode=compile_mode,
        is_pypy=is_pypy,
        walker=walker,
    ).text


if __name__ == "__main__":

    def deparse_test(co):
        "This is a docstring"
        s = deparse_code2str(co)
        # s = deparse_code2str(co, debug_opts={"asm": "after", "tree": {'before': False, 'after': False}})
        print(s)
        return

    deparse_test(deparse_test.func_code)
