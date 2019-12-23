#  Copyright (c) 2019 by Rocky Bernstein

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

from uncompyle6.show import maybe_show_tree
from copy import copy
from spark_parser import GenericASTTraversal, GenericASTTraversalPruningException

from uncompyle6.parsers.treenode import SyntaxTree
from uncompyle6.scanners.tok import Token
from uncompyle6.semantics.consts import RETURN_NONE


def is_docstring(node):
    try:
        return node[0][0].kind == "assign" and node[0][0][1][0].pattr == "__doc__"
    except:
        return False


class TreeTransform(GenericASTTraversal, object):
    def __init__(self, version, show_ast=None,
                is_pypy=False):
        self.version = version
        self.showast = show_ast
        self.is_pypy = is_pypy
        return

    def maybe_show_tree(self, ast):
        if isinstance(self.showast, dict) and self.showast:
            maybe_show_tree(self, ast)

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

    def n_ifstmt(self, node):
        """Here we check if we can turn an `ifstmt` or 'iflaststmtl` into
           some kind of `assert` statement"""

        testexpr = node[0]

        if testexpr.kind != "testexpr":
            return node
        if node.kind in ("ifstmt", "ifstmtl"):
            ifstmts_jump = node[1]

            if ifstmts_jump == "_ifstmts_jumpl" and ifstmts_jump[0] == "_ifstmts_jump":
                ifstmts_jump = ifstmts_jump[0]
            elif ifstmts_jump not in ("_ifstmts_jump", "ifstmts_jumpl"):
                return node
            stmts = ifstmts_jump[0]
        else:
            # iflaststmtl works this way
            stmts = node[1]

        if stmts in ("c_stmts",) and len(stmts) == 1:
            stmt = stmts[0]
            raise_stmt = stmt[0]
            if (
                raise_stmt == "raise_stmt1"
                and len(testexpr[0]) == 2
                and raise_stmt.first_child().pattr == "AssertionError"
            ):
                assert_expr = testexpr[0][0]
                assert_expr.kind = "assert_expr"
                jump_cond = testexpr[0][1]
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
                    if jump_cond == "jmp_true":
                        kind = "assert2"
                    else:
                        assert jump_cond == "jmp_false"
                        kind = "assert2not"

                    LOAD_ASSERT = call[0].first_child()
                    if LOAD_ASSERT != "LOAD_ASSERT":
                        return node
                    if isinstance(call[1], SyntaxTree):
                        expr = call[1][0]
                        node = SyntaxTree(
                            kind,
                            [assert_expr, jump_cond, LOAD_ASSERT, expr, RAISE_VARARGS_1]
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
                    if jump_cond == "jmp_true":
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
                        [assert_expr, jump_cond, LOAD_ASSERT, RAISE_VARARGS_1]
                    )
                node.transformed_by="n_ifstmt",
                pass
            pass
        return node

    n_ifstmtl = n_iflaststmtl = n_ifstmt

    # preprocess is used for handling chains of
    # if elif elif
    def n_ifelsestmt(self, node, preprocess=False):
        """
        Here we turn:

          if ...
          else
             if ..

        into:

          if ..
          elif ...

          [else ...]

        where appropriate
        """
        else_suite = node[3]

        n = else_suite[0]
        old_stmts = None
        else_suite_index = 1

        if len(n) == 1 == len(n[0]) and n[0] == "stmt":
            n = n[0][0]
        elif n[0].kind in ("lastc_stmt", "lastl_stmt"):
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
            pass
        elif len(n) > 1 and 1 == len(n[0]) and n[0] == "stmt" and n[1].kind == "stmt":
            else_suite_stmts = n[0]
            if else_suite_stmts[0].kind not in ("ifstmt", "iflaststmt", "ifelsestmtl"):
                return node
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

    def n_list_for(self, list_for_node):
        expr = list_for_node[0]
        if expr == "expr" and expr[0] == "get_iter":
            # Remove extraneous get_iter() inside the "for" of a comprehension
            assert expr[0][0] == "expr"
            list_for_node[0] = expr[0][0]
            list_for_node.transformed_by = ("n_list_for",)
        return list_for_node

    def traverse(self, node, is_lambda=False):
        node = self.preorder(node)
        return node

    def transform(self, ast):
        self.maybe_show_tree(ast)
        self.ast = copy(ast)
        self.ast = self.traverse(self.ast, is_lambda=False)

        if self.ast[-1] == RETURN_NONE:
            self.ast.pop()  # remove last node
            # todo: if empty, add 'pass'

        return self.ast

    # Write template_engine
    # def template_engine
