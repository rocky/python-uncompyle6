#  Copyright (c) 2022 by Rocky Bernstein
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
Custom Nonterminal action functions. See NonterminalActions docstring.
"""

from uncompyle6.semantics.consts import (
    INDENT_PER_LEVEL,
    NONE,
    PRECEDENCE,
    minint,
)

from uncompyle6.parsers.treenode import SyntaxTree
from uncompyle6.scanners.tok import Token
from uncompyle6.util import better_repr

from uncompyle6.semantics.helper import (
    find_code_node,
    flatten_list,
)


class NonterminalActions:
    """
    Methods here all start with n_ and the remaining portion should be a nonterminal
    name defined by some rule.

    These methods take priority over names defined in table constants.
    All of the methods should have the same signature: (self, node) and return None.

    node is the subtree of the parse tree the that nonterminal name as the root.
    """

    def __init__(self):
        # Precedence is used to determine when an expression needs
        # parenthesis surrounding it. A high value indicates no
        # parenthesis are needed.
        self.prec = 1000

    def n_alias(self, node):
        if self.version <= (2, 1):
            if len(node) == 2:
                store = node[1]
                assert store == "store"
                if store[0].pattr == node[0].pattr:
                    self.write("import %s\n" % node[0].pattr)
                else:
                    self.write("import %s as %s\n" % (node[0].pattr, store[0].pattr))
                    pass
                pass
            self.prune()  # stop recursing

        store_node = node[-1][-1]
        assert store_node.kind.startswith("STORE_")
        iname = node[0].pattr  # import name
        sname = store_node.pattr  # store_name
        if iname and iname == sname or iname.startswith(sname + "."):
            self.write(iname)
        else:
            self.write(iname, " as ", sname)
        self.prune()  # stop recursing

    n_alias37 = n_alias

    def n_assign(self, node):
        # A horrible hack for Python 3.0 .. 3.2
        if (3, 0) <= self.version <= (3, 2) and len(node) == 2:
            if (
                node[0][0] == "LOAD_FAST"
                and node[0][0].pattr == "__locals__"
                and node[1][0].kind == "STORE_LOCALS"
            ):
                self.prune()
        self.default(node)

    def n_assign2(self, node):
        for n in node[-2:]:
            if n[0] == "unpack":
                n[0].kind = "unpack_w_parens"
        self.default(node)

    def n_assign3(self, node):
        for n in node[-3:]:
            if n[0] == "unpack":
                n[0].kind = "unpack_w_parens"
        self.default(node)

    def n_attribute(self, node):
        if node[0] == "LOAD_CONST" or node[0] == "expr" and node[0][0] == "LOAD_CONST":
            # FIXME: I didn't record which constants parenthesis is
            # necessary. However, I suspect that we could further
            # refine this by looking at operator precedence and
            # eval'ing the constant value (pattr) and comparing with
            # the type of the constant.
            node.kind = "attribute_w_parens"
        self.default(node)

    def n_bin_op(self, node):
        """bin_op (formerly "binary_expr") is the Python AST BinOp"""
        self.preorder(node[0])
        self.write(" ")
        self.preorder(node[-1])
        self.write(" ")
        # Try to avoid a trailing parentheses by lowering the priority a little
        self.prec -= 1
        self.preorder(node[1])
        self.prec += 1
        self.prune()

    def n_build_slice2(self, node):
        p = self.prec
        self.prec = 100
        if not node[0].isNone():
            self.preorder(node[0])
        self.write(":")
        if not node[1].isNone():
            self.preorder(node[1])
        self.prec = p
        self.prune()  # stop recursing

    def n_build_slice3(self, node):
        p = self.prec
        self.prec = 100
        if not node[0].isNone():
            self.preorder(node[0])
        self.write(":")
        if not node[1].isNone():
            self.preorder(node[1])
        self.write(":")
        if not node[2].isNone():
            self.preorder(node[2])
        self.prec = p
        self.prune()  # stop recursing

    def n_classdef(self, node):

        if self.version >= (3, 6):
            self.n_classdef36(node)
        elif self.version >= (3, 0):
            self.n_classdef3(node)

        # class definition ('class X(A,B,C):')
        cclass = self.currentclass

        # Pick out various needed bits of information
        # * class_name - the name of the class
        # * subclass_info - the parameters to the class  e.g.
        #      class Foo(bar, baz)
        #             -----------
        # * subclass_code - the code for the subclass body

        if node == "classdefdeco2":
            build_class = node
        else:
            build_class = node[0]
        build_list = build_class[1][0]
        if hasattr(build_class[-3][0], "attr"):
            subclass_code = build_class[-3][0].attr
            class_name = build_class[0].pattr
        elif (
            build_class[-3] == "mkfunc"
            and node == "classdefdeco2"
            and build_class[-3][0] == "load_closure"
        ):
            subclass_code = build_class[-3][1].attr
            class_name = build_class[-3][0][0].pattr
        elif hasattr(node[0][0], "pattr"):
            subclass_code = build_class[-3][1].attr
            class_name = node[0][0].pattr
        else:
            raise "Internal Error n_classdef: cannot find class name"

        if node == "classdefdeco2":
            self.write("\n")
        else:
            self.write("\n\n")

        self.currentclass = str(class_name)
        self.write(self.indent, "class ", self.currentclass)

        self.print_super_classes(build_list)
        self.println(":")

        # class body
        self.indent_more()
        self.build_class(subclass_code)
        self.indent_less()

        self.currentclass = cclass
        if len(self.param_stack) > 1:
            self.write("\n\n")
        else:
            self.write("\n\n\n")

        self.prune()

    n_classdefdeco2 = n_classdef

    def n_const_list(self, node):
        """
        prettyprint a constant dict, list, set or tuple.
        """
        p = self.prec

        lastnodetype = node[2].kind
        flat_elems = node[1]
        is_dict = lastnodetype.endswith("DICT")

        if lastnodetype.endswith("LIST"):
            self.write("[")
            endchar = "]"
        elif lastnodetype.endswith("SET") or is_dict:
            self.write("{")
            endchar = "}"
        else:
            # from trepan.api import debug; debug()
            raise TypeError(
                "Internal Error: n_const_list expects dict, list set, or set; got %s" % lastnodetype
            )

        self.indent_more(INDENT_PER_LEVEL)
        sep = ""
        line_len = len(self.indent)
        if is_dict:
            keys = flat_elems[-1].attr
            assert isinstance(keys, tuple)
            assert len(keys) == len(flat_elems) - 1
            for i, elem in enumerate(flat_elems[:-1]):
                assert elem.kind == "ADD_VALUE"
                try:
                    value = "%r" % elem.pattr
                except Exception:
                    value = elem.pattr
                if elem.linestart is not None:
                    if elem.linestart != self.line_number:
                        next_indent = self.indent + INDENT_PER_LEVEL[:-1]
                        line_len = len(next_indent)
                        sep += "\n" + next_indent
                        self.line_number = elem.linestart
                    else:
                        if sep != "":
                            sep += ", "
                elif line_len > 80:
                    next_indent = self.indent + INDENT_PER_LEVEL[:-1]
                    line_len = len(next_indent)
                    sep += "\n" + next_indent

                sep_key_value = "%s %s: %s" % (sep, repr(keys[i]), value)
                line_len += len(sep_key_value)
                self.write(sep_key_value)
                sep = ", "
        else:
            for elem in flat_elems:
                if elem == "add_value":
                    elem = elem[0]
                if elem == "ADD_VALUE":
                    value = "%r" % elem.pattr
                else:
                    assert elem.kind == "ADD_VALUE_VAR"
                    value = "%s" % elem.pattr

                if elem.linestart is not None:
                    if elem.linestart != self.line_number:
                        next_indent = self.indent + INDENT_PER_LEVEL[:-1]
                        line_len += len(next_indent)
                        sep += "\n" + next_indent
                        self.line_number = elem.linestart
                    else:
                        if sep != "":
                            sep += " "
                        line_len += len(sep)
                elif line_len > 80:
                    next_indent = self.indent + INDENT_PER_LEVEL[:-1]
                    line_len = len(next_indent)
                    sep += "\n" + next_indent

                line_len += len(sep) + len(str(value)) + 1
                self.write(sep, value)
                sep = ", "
        self.write(endchar)
        self.indent_less(INDENT_PER_LEVEL)

        self.prec = p
        self.prune()
        return

    def n_delete_subscript(self, node):
        if node[-2][0] == "build_list" and node[-2][0][-1].kind.startswith(
            "BUILD_TUPLE"
        ):
            if node[-2][0][-1] != "BUILD_TUPLE_0":
                node[-2][0].kind = "build_tuple2"
        self.default(node)

    n_store_subscript = n_subscript = n_delete_subscript

    def n_dict(self, node):
        """
        Prettyprint a dict.
        'dict' is something like k = {'a': 1, 'b': 42}"
        We will use source-code line breaks to guide us when to break.
        """
        if len(node) == 1 and node[0] == "const_list":
            self.preorder(node[0])
            self.prune()
            return

        p = self.prec
        self.prec = 100

        self.indent_more(INDENT_PER_LEVEL)
        sep = INDENT_PER_LEVEL[:-1]
        if node[0] != "dict_entry":
            self.write("{")
        line_number = self.line_number

        if self.version >= (3, 0) and not self.is_pypy:
            if node[0].kind.startswith("kvlist"):
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
                    name = self.traverse(l[i], indent="")
                    if i > 0:
                        line_number = self.indent_if_source_nl(
                            line_number, self.indent + INDENT_PER_LEVEL[:-1]
                        )
                    line_number = self.line_number
                    self.write(name, ": ")
                    value = self.traverse(
                        l[i + 1], indent=self.indent + (len(name) + 2) * " "
                    )
                    self.write(value)
                    sep = ", "
                    if line_number != self.line_number:
                        sep += "\n" + self.indent + INDENT_PER_LEVEL[:-1]
                        line_number = self.line_number
                    i += 2
                    pass
                pass
            elif len(node) > 1 and node[1].kind.startswith("kvlist"):
                # Python 3.0..3.4 style key/value list in dict
                kv_node = node[1]
                l = list(kv_node)
                if len(l) > 0 and l[0].kind == "kv3":
                    # Python 3.2 does this
                    kv_node = node[1][0]
                    l = list(kv_node)
                i = 0
                while i < len(l):
                    self.write(sep)
                    name = self.traverse(l[i + 1], indent="")
                    if i > 0:
                        line_number = self.indent_if_source_nl(
                            line_number, self.indent + INDENT_PER_LEVEL[:-1]
                        )
                        pass
                    line_number = self.line_number
                    self.write(name, ": ")
                    value = self.traverse(
                        l[i], indent=self.indent + (len(name) + 2) * " "
                    )
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
            elif node[-1].kind.startswith("BUILD_CONST_KEY_MAP"):
                # Python 3.6+ style const map
                keys = node[-2].pattr
                values = node[:-2]
                # FIXME: Line numbers?
                for key, value in zip(keys, values):
                    self.write(sep)
                    self.write(repr(key))
                    line_number = self.line_number
                    self.write(":")
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
            elif node[0].kind.startswith("dict_entry"):
                assert self.version >= (3, 5)
                template = ("%C", (0, len(node[0]), ", **"))
                self.template_engine(template, node[0])
                sep = ""
            elif node[-1].kind.startswith("BUILD_MAP_UNPACK") or node[
                -1
            ].kind.startswith("dict_entry"):
                assert self.version >= (3, 5)
                # FIXME: I think we can intermingle dict_comp's with other
                # dictionary kinds of things. The most common though is
                # a sequence of dict_comp's
                kwargs = node[-1].attr
                template = ("**%C", (0, kwargs, ", **"))
                self.template_engine(template, node)
                sep = ""
            if node[0].kind == "COLLECTION_START":
                key_value_pairs = node[1]
                for key_value_pair in key_value_pairs:
                    key, value = key_value_pair
                    if key.linestart is not None:
                        line_number = key.linestart
                    if line_number != self.line_number:
                        sep += "\n" + self.indent + INDENT_PER_LEVEL[:-1]
                        self.line_number = line_number
                    self.write(sep)
                    self.write(key.pattr)
                    self.write(": ")
                    if value.linestart is not None:
                        line_number = value.linestart
                    if line_number != self.line_number:
                        sep += "\n" + self.indent + INDENT_PER_LEVEL[:-1]
                        self.line_number = line_number
                    else:
                        sep += " "
                        pass
                    self.write(value.pattr)
                    sep = ", "
                    pass
                if sep.startswith(",\n"):
                    self.write(sep[1:])
                pass

            pass
        else:
            # Python 2 style kvlist. Find beginning of kvlist.
            indent = self.indent + "  "
            line_number = self.line_number
            if node[0].kind.startswith("BUILD_MAP"):
                if len(node) > 1 and node[1].kind in ("kvlist", "kvlist_n"):
                    kv_node = node[1]
                else:
                    kv_node = node[1:]
                self.kv_map(kv_node, sep, line_number, indent)
            else:
                sep = ""
                opname = node[-1].kind
                if self.is_pypy and self.version >= (3, 5):
                    if opname.startswith("BUILD_CONST_KEY_MAP"):
                        keys = node[-2].attr
                        # FIXME: DRY this and the above
                        for i in range(len(keys)):
                            key = keys[i]
                            value = self.traverse(node[i], indent="")
                            self.write(sep, key, ": ", value)
                            sep = ", "
                            if line_number != self.line_number:
                                sep += "\n" + self.indent + "  "
                                line_number = self.line_number
                                pass
                            pass
                        pass
                    else:
                        if opname.startswith("kvlist"):
                            list_node = node[0]
                        else:
                            list_node = node

                        assert list_node[-1].kind.startswith("BUILD_MAP")
                        for i in range(0, len(list_node) - 1, 2):
                            key = self.traverse(list_node[i], indent="")
                            value = self.traverse(list_node[i + 1], indent="")
                            self.write(sep, key, ": ", value)
                            sep = ", "
                            if line_number != self.line_number:
                                sep += "\n" + self.indent + "  "
                                line_number = self.line_number
                                pass
                            pass
                        pass
                elif opname.startswith("kvlist"):
                    kv_node = node[-1]
                    self.kv_map(node[-1], sep, line_number, indent)

                pass
            pass
        if sep.startswith(",\n"):
            self.write(sep[1:])
        if node[0] != "dict_entry":
            self.write("}")
        self.indent_less(INDENT_PER_LEVEL)
        self.prec = p
        self.prune()

    def n_docstring(self, node):

        indent = self.indent
        doc_node = node[0]
        if doc_node.attr:
            docstring = doc_node.attr
            if not isinstance(docstring, str):
                # FIXME: we have mistakenly tagged something as a doc
                # string in transform when it isn't one.
                # The rule in n_mkfunc is pretty flaky.
                self.prune()
                return
        else:
            docstring = node[0].pattr

        quote = '"""'
        if docstring.find(quote) >= 0:
            if docstring.find("'''") == -1:
                quote = "'''"

        self.write(indent)
        docstring = repr(docstring.expandtabs())[1:-1]

        for (orig, replace) in (
            ("\\\\", "\t"),
            ("\\r\\n", "\n"),
            ("\\n", "\n"),
            ("\\r", "\n"),
            ('\\"', '"'),
            ("\\'", "'"),
        ):
            docstring = docstring.replace(orig, replace)

        # Do a raw string if there are backslashes but no other escaped characters:
        # also check some edge cases
        if (
            "\t" in docstring
            and "\\" not in docstring
            and len(docstring) >= 2
            and docstring[-1] != "\t"
            and (docstring[-1] != '"' or docstring[-2] == "\t")
        ):
            self.write("r")  # raw string
            # Restore backslashes unescaped since raw
            docstring = docstring.replace("\t", "\\")
        else:
            # Escape the last character if it is the same as the
            # triple quote character.
            quote1 = quote[-1]
            if len(docstring) and docstring[-1] == quote1:
                docstring = docstring[:-1] + "\\" + quote1

            # Escape triple quote when needed
            if quote == '"""':
                replace_str = '\\"""'
            else:
                assert quote == "'''"
                replace_str = "\\'''"

            docstring = docstring.replace(quote, replace_str)
            docstring = docstring.replace("\t", "\\\\")

        lines = docstring.split("\n")

        self.write(quote)
        if len(lines) == 0:
            self.println(quote)
        elif len(lines) == 1:
            self.println(lines[0], quote)
        else:
            self.println(lines[0])
            for line in lines[1:-1]:
                if line:
                    self.println(line)
                else:
                    self.println("\n\n")
                    pass
                pass
            self.println(lines[-1], quote)
        self.prune()

    def n_elifelsestmtr(self, node):
        if node[2] == "COME_FROM":
            return_stmts_node = node[3]
            node.kind = "elifelsestmtr2"
        else:
            return_stmts_node = node[2]

        if len(return_stmts_node) != 2:
            self.default(node)

        for n in return_stmts_node[0]:
            if not (n[0] == "ifstmt" and n[0][1][0] == "return_if_stmts"):
                self.default(node)
                return

        self.write(self.indent, "elif ")
        self.preorder(node[0])
        self.println(":")
        self.indent_more()
        self.preorder(node[1])
        self.indent_less()

        for n in return_stmts_node[0]:
            n[0].kind = "elifstmt"
            self.preorder(n)
        self.println(self.indent, "else:")
        self.indent_more()
        self.preorder(return_stmts_node[1])
        self.indent_less()
        self.prune()

    def n_except_cond2(self, node):
        if node[-1] == "come_from_opt":
            unpack_node = -3
        else:
            unpack_node = -2

        if node[unpack_node][0] == "unpack":
            node[unpack_node][0].kind = "unpack_w_parens"
        self.default(node)

    # Note: this node is only in Python 2.x
    # FIXME: figure out how to get this into customization
    # put so that we can get access via super from
    # the fragments routine.
    def n_exec_stmt(self, node):
        """
        exec_stmt ::= expr exprlist DUP_TOP EXEC_STMT
        exec_stmt ::= expr exprlist EXEC_STMT
        """
        self.write(self.indent, "exec ")
        self.preorder(node[0])
        if not node[1][0].isNone():
            sep = " in "
            for subnode in node[1]:
                self.write(sep)
                sep = ", "
                self.preorder(subnode)
        self.println()
        self.prune()  # stop recursing

    def n_expr(self, node):
        first_child = node[0]
        if first_child == "_lambda_body" and self.in_format_string:
            p = -2
        else:
            p = self.prec

        if first_child.kind.startswith("bin_op"):
            n = node[0][-1][0]
        else:
            n = node[0]

        # if (hasattr(n, 'linestart') and n.linestart and
        #     hasattr(self, 'current_line_number')):
        #     self.source_linemap[self.current_line_number] = n.linestart

        self.prec = PRECEDENCE.get(n.kind, -2)
        if n == "LOAD_CONST" and repr(n.pattr)[0] == "-":
            self.prec = 6

        # print("XXX", n.kind, p, "<", self.prec)
        # print(self.f.getvalue())

        if p < self.prec:
            # print(f"PREC {p}, {node[0].kind}")
            self.write("(")
            self.preorder(node[0])
            self.write(")")
        else:
            self.preorder(node[0])
        self.prec = p
        self.prune()

    n_return_expr_or_cond = n_expr

    def n_generator_exp(self, node):
        self.write("(")
        iter_index = 3
        if self.version > (3, 2):
            if self.version >= (3, 6):
                if node[0].kind in ("load_closure", "load_genexpr") and self.version >= (3, 8):
                    code_index = -6
                    is_lambda = self.is_lambda
                    if node[0].kind == "load_genexpr":
                        self.is_lambda = False
                    self.closure_walk(node, collection_index=4)
                    self.is_lambda = is_lambda
                else:
                    # Python 3.7+ adds optional "come_froms" at node[0] so count from the end
                    if node == "generator_exp_async" and self.version[:2] == (3, 6):
                        code_index = 0
                    else:
                        code_index = -6
                    if self.version < (3, 8):
                        iter_index = 4
                    else:
                        iter_index = 3
                    self.comprehension_walk(node, iter_index=iter_index, code_index=code_index)
                    pass
                pass
        else:
            code_index = -5
            self.comprehension_walk(node, iter_index=iter_index, code_index=code_index)
        self.write(")")
        self.prune()

    n_generator_exp_async = n_generator_exp

    def n_ifelsestmtr(self, node):
        if node[2] == "COME_FROM":
            return_stmts_node = node[3]
            node.kind = "ifelsestmtr2"
        else:
            return_stmts_node = node[2]
        if len(return_stmts_node) != 2:
            self.default(node)

        if not (
            return_stmts_node[0][0][0] == "ifstmt"
            and return_stmts_node[0][0][0][1][0] == "return_if_stmts"
        ) and not (
            return_stmts_node[0][-1][0] == "ifstmt"
            and return_stmts_node[0][-1][0][1][0] == "return_if_stmts"
        ):
            self.default(node)
            return

        self.write(self.indent, "if ")
        self.preorder(node[0])
        self.println(":")
        self.indent_more()
        self.preorder(node[1])
        self.indent_less()

        if_ret_at_end = False
        if len(return_stmts_node[0]) >= 3:
            if (
                return_stmts_node[0][-1][0] == "ifstmt"
                and return_stmts_node[0][-1][0][1][0] == "return_if_stmts"
            ):
                if_ret_at_end = True

        past_else = False
        prev_stmt_is_if_ret = True
        for n in return_stmts_node[0]:
            if n[0] == "ifstmt" and n[0][1][0] == "return_if_stmts":
                if prev_stmt_is_if_ret:
                    n[0].kind = "elifstmt"
                prev_stmt_is_if_ret = True
            else:
                prev_stmt_is_if_ret = False
                if not past_else and not if_ret_at_end:
                    self.println(self.indent, "else:")
                    self.indent_more()
                    past_else = True
            self.preorder(n)
        if not past_else or if_ret_at_end:
            self.println(self.indent, "else:")
            self.indent_more()
        self.preorder(return_stmts_node[1])
        self.indent_less()
        self.prune()

    n_ifelsestmtr2 = n_ifelsestmtr

    def n_import_from(self, node):
        relative_path_index = 0
        if self.version >= (2, 5):
            if node[relative_path_index].attr > 0:
                node[2].pattr = ("." * node[relative_path_index].attr) + node[2].pattr
            if self.version > (2, 7):
                if isinstance(node[1].pattr, tuple):
                    imports = node[1].pattr
                    for pattr in imports:
                        node[1].pattr = pattr
                        self.default(node)
                    return
                pass
        self.default(node)

    n_import_from_star = n_import_from

    def n_lambda_body(self, node):
        self.make_function(node, is_lambda=True, code_node=node[-2])
        self.prune()  # stop recursing

    def n_list(self, node):
        """
        prettyprint a dict, list, set or tuple.
        """
        if len(node) == 1 and node[0] == "const_list":
            self.preorder(node[0])
            self.prune()
            return

        p = self.prec
        self.prec = PRECEDENCE["yield"] - 1
        lastnode = node.pop()
        lastnodetype = lastnode.kind

        # If this build list is inside a CALL_FUNCTION_VAR,
        # then the first * has already been printed.
        # Until I have a better way to check for CALL_FUNCTION_VAR,
        # will assume that if the text ends in *.
        last_was_star = self.f.getvalue().endswith("*")

        if lastnodetype.endswith("UNPACK"):
            # FIXME: need to handle range of BUILD_LIST_UNPACK
            have_star = True
            # endchar = ''
        else:
            have_star = False

        if lastnodetype.startswith("BUILD_LIST"):
            self.write("[")
            endchar = "]"
        elif lastnodetype.startswith("BUILD_MAP_UNPACK"):
            self.write("{*")
            endchar = "}"
        elif lastnodetype.startswith("BUILD_SET"):
            self.write("{")
            endchar = "}"
        elif lastnodetype.startswith("BUILD_TUPLE"):
            # Tuples can appear places that can NOT
            # have parenthesis around them, like array
            # subscripts. We check for that by seeing
            # if a tuple item is some sort of slice.
            no_parens = False
            for n in node:
                if n == "expr" and n[0].kind.startswith("build_slice"):
                    no_parens = True
                    break
                pass
            if no_parens:
                endchar = ""
            else:
                self.write("(")
                endchar = ")"
                pass

        elif lastnodetype.startswith("ROT_TWO"):
            self.write("(")
            endchar = ")"
        else:
            raise TypeError(
                "Internal Error: n_build_list expects list, tuple, set, or unpack"
            )

        flat_elems = flatten_list(node)

        self.indent_more(INDENT_PER_LEVEL)
        sep = ""
        for elem in flat_elems:
            if elem in ("ROT_THREE", "EXTENDED_ARG"):
                continue
            assert elem == "expr"
            line_number = self.line_number
            value = self.traverse(elem)
            if line_number != self.line_number:
                sep += "\n" + self.indent + INDENT_PER_LEVEL[:-1]
            else:
                if sep != "":
                    sep += " "
            if not last_was_star:
                if have_star:
                    sep += "*"
                    pass
                pass
            else:
                last_was_star = False
            self.write(sep, value)
            sep = ","
        if lastnode.attr == 1 and lastnodetype.startswith("BUILD_TUPLE"):
            self.write(",")
        self.write(endchar)
        self.indent_less(INDENT_PER_LEVEL)

        self.prec = p
        self.prune()
        return

    n_set = n_tuple = n_build_set = n_list

    def n_list_comp(self, node):
        """List comprehensions"""
        p = self.prec
        self.prec = 100
        if self.version >= (2, 7):
            if self.is_pypy:
                self.n_list_comp_pypy27(node)
                return
            n = node[-1]
        elif node[-1] == "delete":
            if node[-2] == "JUMP_BACK":
                n = node[-3]
            else:
                n = node[-2]

        assert n == "list_iter"

        # Find the list comprehension body. It is the inner-most
        # node that is not list_.. .
        # FIXME: DRY with other use
        while n == "list_iter":
            n = n[0]  # iterate one nesting deeper
            if n == "list_for":
                n = n[3]
            elif n == "list_if":
                n = n[2]
            elif n == "list_if_not":
                n = n[2]
        assert n == "lc_body"
        self.write("[ ")

        if self.version >= (2, 7):
            expr = n[0]
            list_iter = node[-1]
        else:
            expr = n[1]
            if node[-2] == "JUMP_BACK":
                list_iter = node[-3]
            else:
                list_iter = node[-2]

        assert expr == "expr"
        assert list_iter == "list_iter"

        # FIXME: use source line numbers for directing line breaks

        line_number = self.line_number
        last_line = self.f.getvalue().split("\n")[-1]
        l = len(last_line)
        indent = " " * (l - 1)

        self.preorder(expr)
        line_number = self.indent_if_source_nl(line_number, indent)
        self.preorder(list_iter)
        l2 = self.indent_if_source_nl(line_number, indent)
        if l2 != line_number:
            self.write(" " * (len(indent) - len(self.indent) - 1) + "]")
        else:
            self.write(" ]")
        self.prec = p
        self.prune()  # stop recursing

    def n_list_comp_pypy27(self, node):
        """List comprehensions in PYPY."""
        p = self.prec
        self.prec = 27
        if node[-1].kind == "list_iter":
            n = node[-1]
        elif self.is_pypy and node[-1] == "JUMP_BACK":
            n = node[-2]
        list_expr = node[1]

        if len(node) >= 3:
            store = node[3]
        elif self.is_pypy and n[0] == "list_for":
            store = n[0][2]

        assert n == "list_iter"
        assert store == "store"

        # Find the list comprehension body. It is the inner-most
        # node.
        # FIXME: DRY with other use
        while n == "list_iter":
            n = n[0]  # iterate one nesting deeper
            if n == "list_for":
                n = n[3]
            elif n == "list_if":
                n = n[2]
            elif n == "list_if_not":
                n = n[2]
        assert n == "lc_body"
        self.write("[ ")

        expr = n[0]
        if self.is_pypy and node[-1] == "JUMP_BACK":
            list_iter = node[-2]
        else:
            list_iter = node[-1]

        assert expr == "expr"
        assert list_iter == "list_iter"

        # FIXME: use source line numbers for directing line breaks

        self.preorder(expr)
        self.preorder(list_expr)
        self.write(" ]")
        self.prec = p
        self.prune()  # stop recursing

    def n_listcomp(self, node):
        self.write("[")
        if node[0].kind == "load_closure":
            assert self.version >= (3, 0)
            self.listcomp_closure3(node)
        else:
            if node == "listcomp_async":
                list_iter_index = 5
            else:
                list_iter_index = 1
            self.comprehension_walk_newer(node, list_iter_index, 0)
        self.write("]")
        self.prune()

    def n_mkfunc(self, node):

        code_node = find_code_node(node, -2)
        code = code_node.attr
        self.write(code.co_name)
        self.indent_more()

        self.make_function(node, is_lambda=False, code_node=code_node)

        if len(self.param_stack) > 1:
            self.write("\n\n")
        else:
            self.write("\n\n\n")
        self.indent_less()
        self.prune()  # stop recursing

    def n_return(self, node):
        if self.params["is_lambda"]:
            self.preorder(node[0])
            self.prune()
        else:
            # One reason we worry over whether we use "return None" or "return"
            # is that inside a generator, "return None" is illegal.
            # Thank you, Python!
            if self.return_none or not self.is_return_none(node):
                self.default(node)
            else:
                self.template_engine(("%|return\n",), node)

            self.prune()  # stop recursing

    def n_return_expr(self, node):
        if len(node) == 1 and node[0] == "expr":
            # If expr is yield we want parens.
            self.prec = PRECEDENCE["yield"] - 1
            self.n_expr(node[0])
        else:
            self.n_expr(node)

    # Python 3.x can have dead code as a result of its optimization?
    # So we'll add a # at the end of the return lambda so the rest is ignored
    def n_return_expr_lambda(self, node):
        if 1 <= len(node) <= 2:
            self.preorder(node[0])
            self.write(" # Avoid dead code: ")
            self.prune()
        else:
            # We can't comment out like above because there may be a trailing ')'
            # that needs to be written
            assert len(node) == 3 and node[2] in ("RETURN_VALUE_LAMBDA", "LAMBDA_MARKER")
            self.preorder(node[0])
            self.prune()

    def n_return_if_stmt(self, node):
        if self.params["is_lambda"]:
            self.write(" return ")
            self.preorder(node[0])
            self.prune()
        else:
            self.write(self.indent, "return")
            if self.return_none or not self.is_return_none(node):
                self.write(" ")
                self.preorder(node[0])
            self.println()
            self.prune()  # stop recursing

    def n_set_comp(self, node):
        self.write("{")
        if node[0] in ["LOAD_SETCOMP", "LOAD_DICTCOMP"]:
            if self.version == (3, 0):
                iter_index = 6
            else:
                iter_index = 1
            self.comprehension_walk_newer(node, iter_index=iter_index, code_index=0)
        elif node[0].kind == "load_closure" and self.version >= (3, 0):
            self.closure_walk(node, collection_index=4)
        else:
            self.comprehension_walk(node, iter_index=4)
        self.write("}")
        self.prune()

    n_dict_comp = n_set_comp

    # In the old days this node would never get called because
    # it was embedded inside some sort of comprehension
    # Nowadays, we allow starting any code object, not just
    # a top-level module. In doing so we can
    # now encounter this outside of the embedding of
    # a comprehension.
    def n_set_comp_async(self, node):
        self.write("{")
        if node[0] in ["BUILD_SET_0", "BUILD_MAP_0"]:
            self.comprehension_walk_newer(node[1], 3, 0, collection_node=node[1])
        if node[0] in ["LOAD_SETCOMP", "LOAD_DICTCOMP"]:
            get_aiter = node[3]
            assert get_aiter == "get_aiter", node.kind
            self.comprehension_walk_newer(node, 1, 0, collection_node=get_aiter[0])
        self.write("}")
        self.prune()

    n_dict_comp_async = n_set_comp_async

    def n_str(self, node):
        self.write(node[0].pattr)
        self.prune()

    def n_store(self, node):
        expr = node[0]
        if expr == "expr" and expr[0] == "LOAD_CONST" and node[1] == "STORE_ATTR":
            # FIXME: I didn't record which constants parenthesis is
            # necessary. However, I suspect that we could further
            # refine this by looking at operator precedence and
            # eval'ing the constant value (pattr) and comparing with
            # the type of the constant.
            node.kind = "store_w_parens"
        self.default(node)

    def n_unpack(self, node):
        if node[0].kind.startswith("UNPACK_EX"):
            # Python 3+
            before_count, after_count = node[0].attr
            for i in range(before_count + 1):
                self.preorder(node[i])
                if i != 0:
                    self.write(", ")
            self.write("*")
            for i in range(1, after_count + 2):
                self.preorder(node[before_count + i])
                if i != after_count + 1:
                    self.write(", ")
            self.prune()
            return

        if node[0] == "UNPACK_SEQUENCE_0":
            self.write("[]")
            self.prune()
            return

        for n in node[1:]:
            if n[0].kind == "unpack":
                n[0].kind = "unpack_w_parens"

        # In Python 2.4, unpack is used in (a, b, c) of:
        #   except RuntimeError, (a, b, c):
        if self.version < (2, 7):
            node.kind = "unpack_w_parens"
        self.default(node)

    n_unpack_w_parens = n_unpack

    def n_yield(self, node):
        if node != SyntaxTree("yield", [NONE, Token("YIELD_VALUE")]):
            self.template_engine(("yield %c", 0), node)
        elif self.version <= (2, 4):
            # Early versions of Python don't allow a plain "yield"
            self.write("yield None")
        else:
            self.write("yield")

        self.prune()  # stop recursing

    def n_LOAD_CONST(self, node):
        attr = node.attr
        data = node.pattr
        datatype = type(data)
        if isinstance(data, float):
            self.write(better_repr(data, self.version))
        elif isinstance(data, complex):
            self.write(better_repr(data, self.version))
        elif isinstance(datatype, int) and data == minint:
            # convert to hex, since decimal representation
            # would result in 'LOAD_CONST; UNARY_NEGATIVE'
            # change:hG/2002-02-07: this was done for all negative integers
            # todo: check whether this is necessary in Python 2.1
            self.write(hex(data))
        elif datatype is type(Ellipsis):
            self.write("...")
        elif attr is None:
            # LOAD_CONST 'None' only occurs, when None is
            # implicit e.g. in 'return' w/o params
            # pass
            self.write("None")
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
            if isinstance(data, str):
                self.write("b" + repr(data))
            else:
                self.write(repr(data))
        else:
            self.write(repr(data))
        # LOAD_CONST is a terminal, so stop processing/recursing early
        self.prune()
