#  Copyright (c) 2019-2020, 2022 by Rocky Bernstein
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
"""Isolate Python 3.8 version-specific semantic actions here.
"""

########################
# Python 3.8+ changes
#######################

from uncompyle6.semantics.consts import PRECEDENCE, TABLE_DIRECT
from uncompyle6.semantics.customize37 import FSTRING_CONVERSION_MAP
from uncompyle6.semantics.helper import escape_string, strip_quotes

def customize_for_version38(self, version):

    # FIXME: pytest doesn't add proper keys in testing. Reinstate after we have fixed pytest.
    # for lhs in 'for forelsestmt forelselaststmt '
    #             'forelselaststmtc tryfinally38'.split():
    #     del TABLE_DIRECT[lhs]

    TABLE_DIRECT.update(
        {
            "async_for_stmt38": (
                "%|async for %c in %c:\n%+%c%-%-\n\n",
                (2, "store"),
                (0, "expr"),
                (3, ("for_block", "pass")),
            ),
            "async_forelse_stmt38": (
                "%|async for %c in %c:\n%+%c%-%|else:\n%+%c%-\n\n",
                (7, 'store'),
                (0, 'expr'),
                (8, 'for_block'),
                (-1, 'else_suite')
            ),
            "async_with_stmt38": (
                "%|async with %c:\n%+%c%-\n",
                (0, "expr"),
                (7, ("l_stmts_opt", "l_stmts", "pass")),
            ),
            "async_with_as_stmt38": (
                "%|async with %c as %c:\n%+%|%c%-",
                (0, "expr"),
                (6, "store"),
                (7, "suite_stmts"),
            ),
            "c_forelsestmt38": (
                "%|for %c in %c:\n%+%c%-%|else:\n%+%c%-\n\n",
                (2, "store"),
                (0, "expr"),
                (3, "for_block"),
                -1,
            ),
            "c_tryfinallystmt38": (
                "%|try:\n%+%c%-%|finally:\n%+%c%-\n\n",
                (1, "c_suite_stmts_opt"),
                (-2, "c_suite_stmts_opt"),
            ),
            # Python 3.8 reverses the order of keys and items
            # from all prior versions of Python.
            "dict_comp_body": ("%c: %c", (0, "expr"), (1, "expr"),),
            "except_cond1a": ("%|except %c:\n", (1, "expr"),),
            "except_cond_as": (
                "%|except %c as %c:\n",
                (1, "expr"),
                (-2, "STORE_FAST"),
            ),
            "except_handler38": ("%c", (2, "except_stmts")),
            "except_handler38a": ("%c", (-2, "stmts")),
            "except_handler38c": (
                "%c%+%c%-",
                (1, "except_cond1a"),
                (2, "except_stmts"),
            ),
            "except_handler_as": (
                "%c%+\n%+%c%-",
                (1, "except_cond_as"),
                (2, "tryfinallystmt"),
            ),
            "except_ret38a": ("return %c", (4, "expr")),
            # Note: there is a suite_stmts_opt which seems
            # to be bookkeeping which is not expressed in source code
            "except_ret38": ("%|return %c\n", (1, "expr")),
            "for38": (
                "%|for %c in %c:\n%+%c%-\n\n",
                (2, "store"),
                (0, "expr"),
                (3, "for_block"),
            ),
            "forelsestmt38": (
                "%|for %c in %c:\n%+%c%-%|else:\n%+%c%-\n\n",
                (2, "store"),
                (0, "expr"),
                (3, "for_block"),
                -1,
            ),
            "forelselaststmt38": (
                "%|for %c in %c:\n%+%c%-%|else:\n%+%c%-",
                (2, "store"),
                (0, "expr"),
                (3, "for_block"),
                -2,
            ),
            "forelselaststmtc38": (
                "%|for %c in %c:\n%+%c%-%|else:\n%+%c%-\n\n",
                (2, "store"),
                (0, "expr"),
                (3, "for_block"),
                -2,
            ),
            "ifpoplaststmtc": ("%|if %c:\n%+%c%-", (0, "testexpr"), (2, "l_stmts")),
            "pop_return": ("%|return %c\n", (1, "return_expr")),
            "popb_return": ("%|return %c\n", (0, "return_expr")),
            "pop_ex_return": ("%|return %c\n", (0, "return_expr")),
            "set_for": (" for %c in %c", (2, "store"), (0, "expr_or_arg"),),
            "whilestmt38": (
                "%|while %c:\n%+%c%-\n\n",
                (1, ("bool_op", "testexpr", "testexprc")),
                (2, ("l_stmts", "pass")),
            ),
            "whileTruestmt38": (
                "%|while True:\n%+%c%-\n\n",
                (1, ("l_stmts", "pass")),
            ),
            "try_elsestmtl38": (
                "%|try:\n%+%c%-%c%|else:\n%+%c%-",
                (1, "suite_stmts_opt"),
                (3, "except_handler38"),
                (5, "else_suitel"),
            ),
            "try_except38": (
                "%|try:\n%+%c\n%-%|except:\n%+%c%-\n\n",
                (2, ("suite_stmts_opt", "suite_stmts")),
                (3, ("except_handler38a", "except_handler38b", "except_handler38c")),
            ),
            "try_except38r": (
                "%|try:\n%+%c\n%-%|except:\n%+%c%-\n\n",
                (1, "return_except"),
                (2, "except_handler38b"),
            ),
            "try_except38r2": (
                "%|try:\n%+%c\n%-%|except:\n%+%c%c%-\n\n",
                (1, "suite_stmts_opt"),
                (8, "cond_except_stmts_opt"),
                (10, "return"),
            ),
            "try_except38r4": (
                "%|try:\n%+%c\n%-%|except:\n%+%c%c%-\n\n",
                (1, "returns_in_except"),
                (3, "except_cond1"),
                (4, "return"),
            ),
            "try_except_as": (
                "%|try:\n%+%c%-\n%|%-%c\n\n",
                (
                    -4,
                    ("suite_stmts", "_stmts"),
                ),  # Go from the end because of POP_BLOCK variation
                (-3, "except_handler_as"),
            ),
            "try_except_ret38": (
                "%|try:\n%+%c%-\n%|except:\n%+%|%c%-\n\n",
                (1, "returns"),
                (2, "except_ret38a"),
            ),
            "try_except_ret38a": (
                "%|try:\n%+%c%-%c\n\n",
                (1, "returns"),
                (2, "except_handler38c"),
            ),
            "tryfinally38rstmt": (
                "%|try:\n%+%c%-%|finally:\n%+%c%-\n\n",
                (0, "sf_pb_call_returns"),
                (-1, ("ss_end_finally", "suite_stmts", "_stmts")),
            ),
            "tryfinally38rstmt2": (
                "%|try:\n%+%c%-%|finally:\n%+%c%-\n\n",
                (4, "returns"),
                -2,
                "ss_end_finally",
            ),
            "tryfinally38rstmt3": (
                "%|try:\n%+%|return %c%-\n%|finally:\n%+%c%-\n\n",
                (1, "expr"),
                (-1, "ss_end_finally"),
            ),
            "tryfinally38rstmt4": (
                "%|try:\n%+%c%-\n%|finally:\n%+%c%-\n\n",
                (1, "suite_stmts_opt"),
                (5, "suite_stmts_return"),
            ),
            "tryfinally38stmt": (
                "%|try:\n%+%c%-%|finally:\n%+%c%-\n\n",
                (1, "suite_stmts_opt"),
                (6, "suite_stmts_opt"),
            ),
            "tryfinally38astmt": (
                "%|try:\n%+%c%-%|finally:\n%+%c%-\n\n",
                (2, "suite_stmts_opt"),
                (8, "suite_stmts_opt"),
            ),
            "named_expr": (  # AKA "walrus operator"
                "%c := %p",
                (2, "store"),
                (0, "expr", PRECEDENCE["named_expr"] - 1),
            ),
        }
    )

    def except_return_value(node):
        if node[0] == "POP_BLOCK":
            self.default(node[1])
        else:
            self.template_engine(("%|return %c\n", (0, "expr")), node)
        self.prune()

    self.n_except_return_value = except_return_value

    # FIXME: now that we've split out cond_except_stmt,
    # we should be able to get this working as a pure transformation rule,
    # so no procedure is needed here.
    def try_except38r3(node):
        self.template_engine(("%|try:\n%+%c\n%-", (1, "suite_stmts_opt")), node)
        cond_except_stmts_opt = node[5]
        assert cond_except_stmts_opt == "cond_except_stmts_opt"
        for child in cond_except_stmts_opt:
            if child == "cond_except_stmt":
                if child[0] == "except_cond1":
                    self.template_engine(
                        ("%c\n", (0, "except_cond1"), (1, "expr")), child
                    )
                    self.template_engine(("%+%c%-\n", (1, "except_stmts")), child)
                pass
            pass
        self.template_engine(("%+%c%-\n", (7, "return")), node)
        self.prune()

    self.n_try_except38r3 = try_except38r3

    def n_list_afor(node):
        if len(node) == 2:
            # list_afor ::= get_iter list_afor
            self.comprehension_walk_newer(node, 0)
        else:
            list_iter_index = 2 if node[2] == "list_iter" else 3
            self.template_engine(
                (
                    " async for %[1]{%c} in %c%[1]{%c}",
                    (1, "store"),
                    (0, "get_aiter"),
                    (list_iter_index, "list_iter"),
                ),
                node,
            )
        self.prune()

    self.n_list_afor = n_list_afor

    def n_set_afor(node):
        if len(node) == 2:
            self.template_engine(
                (" async for %[1]{%c} in %c", (1, "store"), (0, "get_aiter")), node
            )
        else:
            self.template_engine(
                " async for %[1]{%c} in %c%c",
                (1, "store"),
                (0, "get_aiter"),
                (2, "set_iter"),
            )
        self.prune()

    self.n_set_afor = n_set_afor

    def n_formatted_value_debug(node):
        p = self.prec
        self.prec = 100

        formatted_value = node[1]
        value_equal = node[0].attr
        assert formatted_value.kind.startswith("formatted_value")
        old_in_format_string = self.in_format_string
        self.in_format_string = formatted_value.kind
        format_value_attr = node[-1]

        post_str = ""
        if node[-1] == "BUILD_STRING_3":
            post_load_str = node[-2]
            post_str = self.traverse(post_load_str, indent="")
            post_str = strip_quotes(post_str)

        if format_value_attr == "FORMAT_VALUE_ATTR":
            attr = format_value_attr.attr
            if attr & 4:
                fmt = strip_quotes(self.traverse(node[3], indent=""))
                attr_flags = attr & 3
                if attr_flags:
                    conversion = "%s:%s" % (
                        FSTRING_CONVERSION_MAP.get(attr_flags, ""),
                        fmt,
                    )
                else:
                    conversion = ":%s" % fmt
            else:
                conversion = FSTRING_CONVERSION_MAP.get(attr, "")
            f_str = "f%s" % escape_string(
                "{%s%s}%s" % (value_equal, conversion, post_str)
            )
        else:
            f_conversion = self.traverse(formatted_value, indent="")
            # Remove leaving "f" and quotes
            conversion = strip_quotes(f_conversion[1:])
            f_str = "f%s" % escape_string(("%s%s" % (value_equal, conversion)) + post_str)

        self.write(f_str)
        self.in_format_string = old_in_format_string

        self.prec = p
        self.prune()

    self.n_formatted_value_debug = n_formatted_value_debug

    def n_suite_stmts_return(node):
        if len(node) > 1:
            assert len(node) == 2
            self.template_engine(
                ("%c\n%|return %c", (0, ("_stmts", "suite_stmts")), (1, "expr")), node
            )
        else:
            self.template_engine(("%|return %c", (0, "expr")), node)
        self.prune()

    self.n_suite_stmts_return = n_suite_stmts_return
