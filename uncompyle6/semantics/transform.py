#  Copyright (c) 2019-2024 by Rocky Bernstein

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

from copy import copy
from typing import Optional

from spark_parser import GenericASTTraversal, GenericASTTraversalPruningException

from uncompyle6.parsers.treenode import SyntaxTree
from uncompyle6.scanners.tok import NoneToken, Token
from uncompyle6.semantics.consts import ASSIGN_DOC_STRING, RETURN_NONE
from uncompyle6.semantics.helper import find_code_node
from uncompyle6.show import maybe_show_tree


def is_docstring(node, version, co_consts):
    if node == "sstmt":
        node = node[0]
    # TODO: the test below on 2.7 succeeds for
    #   class OldClass:
    #     __doc__ = DocDescr()
    # which produces:
    #
    #   assign (2)
    #      0. expr
    #         call (2)
    #              0. expr
    #                  L.  16         6  LOAD_DEREF            0  'DocDescr'
    #              1.                 9  CALL_FUNCTION_0       0  None
    #      1. store
    #
    # See Python 2.7 test_descr.py

    # If ASSIGN_DOC_STRING doesn't work we need something like the below
    # but more elaborate to address the above.

    # try:
    #     return node.kind == "assign" and node[1][0].pattr == "__doc__"
    # except:
    #     return False
    if version <= (2, 7):
        doc_load = "LOAD_CONST"
    else:
        doc_load = "LOAD_STR"
    return node == ASSIGN_DOC_STRING(co_consts[0], doc_load)


def is_not_docstring(call_stmt_node) -> bool:
    try:
        return (
            call_stmt_node == "call_stmt"
            and call_stmt_node[0][0] == "LOAD_STR"
            and call_stmt_node[1] == "POP_TOP"
        )
    except Exception:
        return False


class TreeTransform(GenericASTTraversal, object):
    def __init__(
        self,
        version: tuple,
        is_pypy=False,
        show_ast: Optional[dict] = None,
    ):
        self.version = version
        self.showast = show_ast
        self.is_pypy = is_pypy
        return

    def maybe_show_tree(self, tree):
        if isinstance(self.showast, dict) and (
            self.showast.get("before") or self.showast.get("after")
        ):
            maybe_show_tree(self, tree)

    def preorder(self, node=None):
        """Walk the tree in roughly 'preorder' (a bit of a lie explained below).
        For each node with typestring name *name* if the
        node has a method called n_*name*, call that before walking
        children.

        In typical use a node with children can call "preorder" in any
        order it wants which may skip children or order then in ways
        other than first to last.  In fact, this this happens.  So in
        this sense this function not strictly preorder.
        """
        if node is None:
            node = self.ast

        try:
            name = "n_" + self.typestring(node)
            if hasattr(self, name):
                func = getattr(self, name)
                node = func(node)
        except GenericASTTraversalPruningException:
            return

        for i, kid in enumerate(node):
            node[i] = self.preorder(kid)
        return node

    def n_mkfunc(self, node):
        """If the function has a docstring (this is found in the code
        constants), pull that out and make it part of the syntax
        tree. When generating the source string that AST node rather
        than the code field is seen and used.
        """

        if self.version >= (3, 7):
            code_index = -3
        else:
            code_index = -2

        code = find_code_node(node, code_index).attr

        mkfunc_pattr = node[-1].pattr
        if isinstance(mkfunc_pattr, tuple):
            assert isinstance(mkfunc_pattr, tuple)
            assert len(mkfunc_pattr) == 4 and isinstance(mkfunc_pattr, int)

        if len(code.co_consts) > 0 and isinstance(code.co_consts[0], str):
            docstring_node = SyntaxTree(
                "docstring", [Token("LOAD_STR", has_arg=True, pattr=code.co_consts[0])]
            )
            docstring_node.transformed_by = "n_mkfunc"
            node = SyntaxTree("mkfunc", node[:-1] + [docstring_node, node[-1]])
            node.transformed_by = "n_mkfunc"

        return node

    def n_ifstmt(self, node):
        """Here we check if we can turn an `ifstmt` or 'iflaststmtl` into
        some kind of `assert` statement"""

        testexpr = node[0]

        if testexpr not in ("testexpr", "testexprl"):
            return node

        if node.kind in ("ifstmt", "ifstmtl"):
            ifstmts_jump = node[1]

            if ifstmts_jump == "_ifstmts_jumpl" and ifstmts_jump[0] == "_ifstmts_jump":
                ifstmts_jump = ifstmts_jump[0]
            elif ifstmts_jump not in (
                "_ifstmts_jump",
                "_ifstmts_jumpl",
                "ifstmts_jumpl",
            ):
                return node
            stmts = ifstmts_jump[0]
        else:
            # iflaststmtl works this way
            stmts = node[1]

        if stmts in ("c_stmts", "stmts", "stmts_opt") and len(stmts) == 1:
            raise_stmt = stmts[0]
            if raise_stmt != "raise_stmt1" and len(raise_stmt) > 0:
                raise_stmt = raise_stmt[0]

            testtrue_or_false = testexpr[0]
            if (
                raise_stmt.kind == "raise_stmt1"
                and 1 <= len(testtrue_or_false) <= 2
                and raise_stmt.first_child().pattr == "AssertionError"
            ):
                if testtrue_or_false in ("testtrue", "testtruel"):
                    # Skip over the testtrue because because it would
                    # produce a "not" and we don't want that here.
                    assert_expr = testtrue_or_false[0]
                    jump_cond = NoneToken
                else:
                    assert testtrue_or_false in ("testfalse", "testfalsel")
                    assert_expr = testtrue_or_false[0]
                    if assert_expr in ("testfalse_not_and", "and_not"):
                        # FIXME: come back to stuff like this
                        return node

                    jump_cond = testtrue_or_false[1]
                    assert_expr.kind = "assert_expr"
                    pass

                expr = raise_stmt[0]
                RAISE_VARARGS_1 = raise_stmt[1]
                call = expr[0]
                if call == "call":
                    # ifstmt
                    #     0. testexpr
                    #         testtrue (2)
                    #             0. expr
                    #     1. _ifstmts_jump (2)
                    #         0. c_stmts
                    #             stmt
                    #                 raise_stmt1 (2)
                    #                     0. expr
                    #                         call (3)
                    #                     1. RAISE_VARARGS_1
                    # becomes:
                    # assert2 ::= assert_expr jmp_true LOAD_ASSERT expr RAISE_VARARGS_1 COME_FROM
                    if jump_cond in ("jmp_true", NoneToken):
                        kind = "assert2"
                    else:
                        if jump_cond == "jmp_false":
                            # FIXME: We don't handle this kind of thing yet.
                            return node
                        kind = "assert2not"

                    LOAD_ASSERT = call[0].first_child()
                    if LOAD_ASSERT not in ("LOAD_ASSERT", "LOAD_GLOBAL"):
                        return node
                    if isinstance(call[1], SyntaxTree):
                        expr = call[1][0]
                        assert_expr.transformed_by = "n_ifstmt"
                        node = SyntaxTree(
                            kind,
                            [
                                assert_expr,
                                jump_cond,
                                LOAD_ASSERT,
                                expr,
                                RAISE_VARARGS_1,
                            ],
                            transformed_by="n_ifstmt",
                        )
                        pass
                    pass
                else:
                    # ifstmt
                    #   0. testexpr (2)
                    #      testtrue
                    #       0. expr
                    #   1. _ifstmts_jump (2)
                    #      0. c_stmts
                    #        stmts
                    #           raise_stmt1 (2)
                    #             0. expr
                    #                  LOAD_ASSERT
                    #             1.   RAISE_VARARGS_1
                    # becomes:
                    # assert ::= assert_expr jmp_true LOAD_ASSERT RAISE_VARARGS_1 COME_FROM
                    if jump_cond in ("jmp_true", NoneToken):
                        if self.is_pypy:
                            kind = "assert0_pypy"
                        else:
                            kind = "assert"
                    else:
                        assert jump_cond == "jmp_false"
                        kind = "assertnot"

                    LOAD_ASSERT = expr[0]
                    node = SyntaxTree(
                        kind,
                        [assert_expr, jump_cond, LOAD_ASSERT, RAISE_VARARGS_1],
                        transformed_by="n_ifstmt",
                    )
                pass
            pass
        return node

    n_ifstmtl = n_iflaststmtl = n_ifstmt

    # preprocess is used for handling chains of
    # if elif elif
    def n_ifelsestmt(self, node, preprocess=False):
        """
        Transformation involving if..else statements.
        For example


          if ...
          else
             if ..

        into:

          if ..
          elif ...

          [else ...]

        where appropriate.
        """

        else_suite = node[3]

        n = else_suite[0]
        old_stmts = None
        else_suite_index = 1

        len_n = len(n)
        # Sometimes stmt  is reduced away and n[0] can be a single reduction like continue -> CONTINUE.
        if (
            len_n == 1
            and isinstance(n[0], SyntaxTree)
            and len(n[0]) == 1
            and n[0] == "stmt"
        ):
            n = n[0][0]
        elif len_n == 0:
            return node

        if n[0].kind in ("lastc_stmt", "lastl_stmt"):
            n = n[0]

        if n[0].kind in (
            "ifstmt",
            "iflaststmt",
            "iflaststmtl",
            "ifelsestmtl",
            "ifelsestmtc",
            "ifpoplaststmtl",
        ):
            n = n[0]
            if n.kind == "ifpoplaststmtl":
                old_stmts = n[2]
                else_suite_index = 2
            pass
        else:
            if (
                len_n > 1
                and isinstance(n[0], SyntaxTree)
                and 1 == len(n[0])
                and n[0] == "stmt"
                and n[1].kind == "stmt"
            ):
                else_suite_stmts = n[0]
            elif len_n == 1:
                else_suite_stmts = n
            else:
                return node

            if else_suite_stmts[0].kind in (
                "ifstmt",
                "iflaststmt",
                "ifelsestmt",
                "ifelsestmtl",
            ):
                old_stmts = n
                n = else_suite_stmts[0]
            else:
                return node

        if n.kind in ("ifstmt", "iflaststmt", "iflaststmtl", "ifpoplaststmtl"):
            node.kind = "ifelifstmt"
            n.kind = "elifstmt"
        elif n.kind in ("ifelsestmtr",):
            node.kind = "ifelifstmt"
            n.kind = "elifelsestmtr"
        elif n.kind in ("ifelsestmt", "ifelsestmtc", "ifelsestmtl"):
            node.kind = "ifelifstmt"
            self.n_ifelsestmt(n, preprocess=True)
            if n == "ifelifstmt":
                n.kind = "elifelifstmt"
            elif n.kind in ("ifelsestmt", "ifelsestmtc", "ifelsestmtl"):
                n.kind = "elifelsestmt"
        if not preprocess:
            if old_stmts:
                if n.kind == "elifstmt":
                    trailing_else = SyntaxTree("stmts", old_stmts[1:])
                    if len(trailing_else):
                        # We use elifelsestmtr because it has 3 nodes
                        elifelse_stmt = SyntaxTree(
                            "elifelsestmtr", [n[0], n[else_suite_index], trailing_else]
                        )
                        node[3] = elifelse_stmt
                    else:
                        elif_stmt = SyntaxTree("elifstmt", [n[0], n[else_suite_index]])
                        node[3] = elif_stmt

                    node.transformed_by = "n_ifelsestmt"
                    pass
                else:
                    # Other cases for n.kind may happen here
                    pass
                pass
            return node

    n_ifelsestmtc = n_ifelsestmtl = n_ifelsestmt

    def n_import_from37(self, node):
        importlist37 = node[3]
        if importlist37 != "importlist37":
            return node
        if len(importlist37) == 1 and importlist37 == "importlist37":
            alias37 = importlist37[0]
            store = alias37[1]
            assert store == "store"
            alias_name = store[0].attr
            import_name_attr = node[2]
            assert import_name_attr == "IMPORT_NAME_ATTR"
            dotted_names = import_name_attr.attr.split(".")
            if len(dotted_names) > 1 and dotted_names[-1] == alias_name:
                # Simulate:
                # Instead of
                # import_from37 ::= LOAD_CONST LOAD_CONST IMPORT_NAME_ATTR importlist37 POP_TOP
                # import_as37   ::= LOAD_CONST LOAD_CONST importlist37 store POP_TOP
                # 'import_as37':     ( '%|import %c as %c\n', 2, -2),
                node = SyntaxTree(
                    "import_as37",
                    [node[0], node[1], import_name_attr, store, node[-1]],
                    transformed_by="n_import_from37",
                )
                pass
            pass
        return node

    def n_list_for(self, list_for_node):
        expr = list_for_node[0]
        if expr == "expr" and expr[0] == "get_iter":
            # Remove extraneous get_iter() inside the "for" of a comprehension
            assert expr[0][0] == "expr"
            list_for_node[0] = expr[0][0]
            list_for_node.transformed_by = ("n_list_for",)
        return list_for_node

    def n_negated_testtrue(self, node):
        assert node[0] == "testtrue"
        test_node = node[0][0]
        test_node.transformed_by = "n_negated_testtrue"
        return test_node

    def n_stmts(self, node):
        if node.first_child() == "SETUP_ANNOTATIONS":
            prev = node[0][0]
            new_stmts = [node[0]]
            for i, sstmt in enumerate(node[1:]):
                ann_assign = sstmt[0]
                if ann_assign == "ann_assign" and prev == "assign":
                    annotate_var = ann_assign[-2]
                    if annotate_var.attr == prev[-1][0].attr:
                        node[i].kind = "deleted " + node[i].kind
                        del new_stmts[-1]
                        ann_assign_init = SyntaxTree(
                            "ann_assign_init",
                            [ann_assign[0], copy(prev[0]), annotate_var],
                        )
                        if sstmt[0] == "ann_assign":
                            sstmt[0] = ann_assign_init
                        else:
                            sstmt[0][0] = ann_assign_init
                        sstmt[0].transformed_by = "n_stmts"
                        pass
                    pass
                new_stmts.append(sstmt)
                prev = ann_assign
                pass
            node.data = new_stmts
        return node

    def traverse(self, node, is_lambda=False):
        node = self.preorder(node)
        return node

    def transform(self, parse_tree: GenericASTTraversal, code) -> GenericASTTraversal:
        self.maybe_show_tree(parse_tree)
        self.ast = copy(parse_tree)
        del parse_tree
        self.ast = self.traverse(self.ast, is_lambda=False)
        n = len(self.ast)

        try:
            # Disambiguate a string (expression) which appears as a "call_stmt" at
            # the beginning of a function versus a docstring. Seems pretty academic,
            # but this is Python.
            call_stmt = self.ast[0][0]
            if is_not_docstring(call_stmt):
                call_stmt.kind = "string_at_beginning"
                call_stmt.transformed_by = "transform"
                pass
        except Exception:
            pass

        try:
            for i in range(n):
                sstmt = self.ast[i]
                if len(sstmt) == 1 and sstmt == "sstmt":
                    self.ast[i] = self.ast[i][0]

                if is_docstring(self.ast[i], self.version, code.co_consts):
                    load_const = copy(self.ast[i].first_child())
                    store_name = copy(self.ast[i].last_child())
                    docstring_ast = SyntaxTree("docstring", [load_const, store_name])
                    docstring_ast.transformed_by = "transform"
                    del self.ast[i]
                    self.ast.insert(0, docstring_ast)
                    break

            if self.ast[-1] == RETURN_NONE:
                self.ast.pop()  # remove last node
                # todo: if empty, add 'pass'
        except Exception:
            pass

        return self.ast

    # Write template_engine
    # def template_engine
