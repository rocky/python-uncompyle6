#  Copyright (c) 2019-2020 by Rocky Bernstein
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
"""Isolate Python 3.7 version-specific semantic actions here.
"""

from uncompyle6.semantics.consts import (
    PRECEDENCE,
    TABLE_DIRECT,
    maxint,
)

def customize_for_version37(self, version):
    ########################
    # Python 3.7+ changes
    #######################

    PRECEDENCE["attribute37"] = 2
    PRECEDENCE["call_ex"] = 1
    PRECEDENCE["call_ex_kw"] = 1
    PRECEDENCE["call_ex_kw2"] = 1
    PRECEDENCE["call_ex_kw3"] = 1
    PRECEDENCE["call_ex_kw4"] = 1
    PRECEDENCE["call_kw"] = 0
    PRECEDENCE["call_kw36"] = 1
    PRECEDENCE["formatted_value1"] = 100
    PRECEDENCE["if_exp_37a"] = 28
    PRECEDENCE["if_exp_37b"] = 28
    PRECEDENCE["unmap_dict"] = 0

    TABLE_DIRECT.update(
        {
            "and_not": ("%c and not %c", (0, "expr"), (2, "expr")),
            "ann_assign": (
                "%|%[2]{attr}: %c\n", 0,
            ),
            "ann_assign_init": (
                "%|%[2]{attr}: %c = %c\n", 0, 1,
            ),
            "async_for_stmt": (
                "%|async for %c in %c:\n%+%c%-\n\n",
                (7, "store"),
                (1, "expr"),
                (17, "for_block"),
            ),
            "async_for_stmt36": (
                "%|async for %c in %c:\n%+%c%-%-\n\n",
                (9, "store"),
                (1, "expr"),
                (18, "for_block"),
            ),
            "async_for_stmt37": (
                "%|async for %c in %c:\n%+%c%-%-\n\n",
                (7, "store"),
                (1, "expr"),
                (16, "for_block"),
            ),
            "async_with_stmt": ("%|async with %c:\n%+%c%-", (0, "expr"), 7),
            "async_with_as_stmt": (
                "%|async with %c as %c:\n%+%c%-",
                (0, "expr"),
                (6, "store"),
                7,
            ),
            "async_forelse_stmt": (
                "%|async for %c in %c:\n%+%c%-%|else:\n%+%c%-\n\n",
                (7, "store"),
                (1, "expr"),
                (17, "for_block"),
                (25, "else_suite"),
            ),
            "attribute37": ("%c.%[1]{pattr}", 0),
            "attributes37": ("%[0]{pattr} import %c",
                            (0, "IMPORT_NAME_ATTR"),
                            (1, "IMPORT_FROM")),
            "await_expr": ("await %c", 0),
            "await_stmt": ("%|%c\n", 0),
            "call_ex": ("%c(%p)", (0, "expr"), (1, 100)),
            "compare_chained1a_37": (
                ' %[3]{pattr.replace("-", " ")} %p %p',
                (0, 19),
                (-4, 19),
            ),
            "compare_chained1_false_37": (
                ' %[3]{pattr.replace("-", " ")} %p %p',
                (0, 19),
                (-4, 19),
            ),
            "compare_chained2_false_37": (
                ' %[3]{pattr.replace("-", " ")} %p %p',
                (0, 19),
                (-5, 19),
            ),
            "compare_chained1b_false_37": (
                ' %[3]{pattr.replace("-", " ")} %p %p',
                (0, 19),
                (-4, 19),
            ),
            "compare_chained1c_37": (
                ' %[3]{pattr.replace("-", " ")} %p %p',
                (0, 19),
                (-2, 19),
            ),
            "compare_chained2a_37": ('%[1]{pattr.replace("-", " ")} %p', (0, 19)),
            "compare_chained2b_false_37": ('%[1]{pattr.replace("-", " ")} %p', (0, 19)),
            "compare_chained2a_false_37": ('%[1]{pattr.replace("-", " ")} %p', (0, 19)),
            "compare_chained2c_37": (
                '%[3]{pattr.replace("-", " ")} %p %p',
                (0, 19),
                (6, 19),
            ),
            "except_return": ("%|except:\n%+%c%-", 3),
            "if_exp_37a": (
                "%p if %p else %p",
                (1, "expr", 27),
                (0, 27),
                (4, "expr", 27),
            ),
            "if_exp_37b": (
                "%p if %p else %p",
                (2, "expr", 27),
                (0, "expr", 27),
                (5, "expr", 27),
            ),
            "ifstmtl": ("%|if %c:\n%+%c%-", (0, "testexpr"), (1, "_ifstmts_jumpl")),
            'import_as37':     ( '%|import %c as %c\n', 2, -2),
            'import_from37':   ( '%|from %[2]{pattr} import %c\n',
                                 (3, 'importlist37') ),

            "importattr37": ("%c", (0, "IMPORT_NAME_ATTR")),
            "importlist37": ("%C", (0, maxint, ", ")),
            "list_if37": (" if %p%c", (0, 27), 1),
            "list_if37_not": (" if not %p%c", (0, 27), 1),
            "testfalse_not_or": ("not %c or %c", (0, "expr"), (2, "expr")),
            "testfalse_not_and": ("not (%c)", 0),
            "try_except36": ("%|try:\n%+%c%-%c\n\n", 1, -2),
            "tryfinally36": ("%|try:\n%+%c%-%|finally:\n%+%c%-\n\n", (1, "returns"), 3),
            "unmap_dict": ("{**%C}", (0, -1, ", **")),
            "unpack_list": ("*%c", (0, "list")),
            "yield_from": ("yield from %c", (0, "expr")),
        }
    )

    def n_importlist37(node):
        if len(node) == 1:
            self.default(node)
            return
        n = len(node) - 1
        for i in range(n, -1, -1):
            if node[i] != "ROT_TWO":
                break
        self.template_engine(("%C", (0, i + 1, ', ')), node)
        self.prune()
        return

    self.n_importlist37 = n_importlist37
