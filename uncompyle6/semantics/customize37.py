#  Copyright (c) 2019-2022 by Rocky Bernstein
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

import re
from uncompyle6.semantics.consts import (
    PRECEDENCE,
    TABLE_DIRECT,
    INDENT_PER_LEVEL,
)

from uncompyle6.semantics.helper import flatten_list

FSTRING_CONVERSION_MAP = {1: "!s", 2: "!r", 3: "!a", "X": ":X"}


#######################
def customize_for_version37(self, version):
    ########################
    # Python 3.7+ changes
    #######################

    # fmt: off
    PRECEDENCE["attribute37"]      =   2
    PRECEDENCE["call_ex"]          =   1
    PRECEDENCE["call_ex_kw"]       =   1
    PRECEDENCE["call_ex_kw2"]      =   1
    PRECEDENCE["call_ex_kw3"]      =   1
    PRECEDENCE["call_ex_kw4"]      =   1
    PRECEDENCE["call_kw"]          =   0
    PRECEDENCE["call_kw36"]        =   1
    PRECEDENCE["formatted_value1"] =  38  # f"...". This has to be below "named_expr" to make
                                          # f'{(x := 10)}' preserve parenthesis
    PRECEDENCE["formatted_value2"] =  38  # See above
    PRECEDENCE["if_exp_37a"]       =  28
    PRECEDENCE["if_exp_37b"]       =  28
    PRECEDENCE["dict_unpack"]      =   0  # **{...}

    # fmt: on
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
            "async_for_stmt37": (
                "%|async for %c in %c:\n%+%c%-\n\n",
                (8, "store"),
                (1, "expr"),
                (17, ("for_block", "pass")),
            ),
            "async_with_stmt": ("%|async with %c:\n%+%c%-", (0, "expr"), 3),
            "async_with_as_stmt": (
                "%|async with %c as %c:\n%+%c%-",
                (0, "expr"),
                (2, "store"),
                3,
            ),
            "async_forelse_stmt": (
                "%|async for %c in %c:\n%+%c%-%|else:\n%+%c%-\n\n",
                (8, "store"),
                (1, "expr"),
                (-10, "for_block"),
                (-2, "else_suite"),
            ),
            "attribute37": ("%c.%[1]{pattr}", (0, "expr")),
            "attributes37": (
                "%[0]{pattr} import %c",
                (0, "IMPORT_NAME_ATTR"),
                (1, "IMPORT_FROM")
            ),

            # nested await expressions like:
            #   return await (await bar())
            # need parenthesis.
            # Note there are async dictionary expressions are like await expr's
            # the below is just the default fersion
            "await_expr": ("await %p", (0, PRECEDENCE["await_expr"] - 1)),
            "await_stmt": ("%|%c\n", 0),
            "c_async_with_stmt": ("%|async with %c:\n%+%c%-", (0, "expr"), 3),
            "call_ex": ("%c(%p)", (0, "expr"), (1, 100)),
            "compare_chained1a_37": (
                ' %[3]{pattr.replace("-", " ")} %p %p',
                (0, PRECEDENCE["compare"] - 1),
                (-4, PRECEDENCE["compare"] - 1),
            ),
            "compare_chained1_false_37": (
                ' %[3]{pattr.replace("-", " ")} %p %p',
                (0, PRECEDENCE["compare"] - 1),
                (-4, PRECEDENCE["compare"] - 1),
            ),
            "compare_chained2_false_37": (
                ' %[3]{pattr.replace("-", " ")} %p %p',
                (0, PRECEDENCE["compare"] - 1),
                (-5, PRECEDENCE["compare"] - 1),
            ),
            "compare_chained1b_false_37": (
                ' %[3]{pattr.replace("-", " ")} %p %p',
                (0, PRECEDENCE["compare"] - 1),
                (-4, PRECEDENCE["compare"] - 1),
            ),
            "compare_chained1c_37": (
                ' %[3]{pattr.replace("-", " ")} %p %p',
                (0, PRECEDENCE["compare"] - 1),
                (-2, PRECEDENCE["compare"] - 1),
            ),
            "compare_chained2a_37": ('%[1]{pattr.replace("-", " ")} %p', (0, PRECEDENCE["compare"] - 1)),
            "compare_chained2b_false_37": ('%[1]{pattr.replace("-", " ")} %p', (0, PRECEDENCE["compare"] - 1)),
            "compare_chained2a_false_37": ('%[1]{pattr.replace("-", " ")} %p', (0, PRECEDENCE["compare"] - 1)),
            "compare_chained2c_37": (
                '%[3]{pattr.replace("-", " ")} %p %p',
                (0, PRECEDENCE["compare"] - 1),
                (6, PRECEDENCE["compare"] - 1),
            ),
            'if_exp37': (
                '%p if %c else %c',
                (1, 'expr', 27), 0, 3
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
            'import_as37': (
                "%|import %c as %c\n", 2, -2
            ),
            "import_from37": ("%|from %[2]{pattr} import %c\n", (3, "importlist37")),
            "import_from_as37": (
                "%|from %c as %c\n",
                (2, "import_from_attr37"),
                (3, "store"),
            ),
            "import_one": (
                "%c",
                (0, "importlists"),
            ),
            "importattr37": ("%c", (0, "IMPORT_NAME_ATTR")),
            "import_from_attr37": (
                "%c import %c",
                (0, "IMPORT_NAME_ATTR"),
                (1, "IMPORT_FROM"),
            ),
            "list_afor": (
                " async for %[1]{%c} in %c%[1]{%c}",
                (1, "store"),
                (0, "get_aiter"),
                (3, "list_iter"),
            ),

            "list_if37": (" if %p%c", (0, 27), 1),
            "list_if37_not": (" if not %p%c", (0, 27), 1),
            "testfalse_not_or": ("not %c or %c", (0, "expr"), (2, "expr")),
            "testfalse_not_and": ("not (%c)", 0),
            "testfalsel":  ("not %c", (0, "expr")),
            "try_except36": ("%|try:\n%+%c%-%c\n\n", 1, -2),
            "tryfinally36": ("%|try:\n%+%c%-%|finally:\n%+%c%-\n\n", (1, "returns"), 3),
            "dict_unpack": ("{**%C}", (0, -1, ", **")),
            "unpack_list": ("*%c", (0, "list")),
            "yield_from": ("yield from %c", (0, "expr")),
        }
    )
    # fmt: on

    def gen_function_parens_adjust(mapping_key, node):
        """If we can avoid the outer parenthesis
        of a generator function, set the node key to
        'call_generator' and the caller will do the default
        action on that. Otherwise we do nothing.
        """
        if mapping_key.kind != "CALL_FUNCTION_1":
            return

        args_node = node[-2]
        if args_node == "pos_arg":
            assert args_node[0] == "expr"
            n = args_node[0][0]
            if n == "generator_exp":
                node.kind = "call_generator"
            pass
        return

    def n_assert_invert(node):
        testtrue = node[0]
        assert testtrue == "testtrue"
        testtrue.kind = "assert"
        self.default(testtrue)

    self.n_assert_invert = n_assert_invert

    def n_async_call(node):
        self.f.write("async ")
        node.kind = "call"
        p = self.prec
        self.prec = 80
        self.template_engine(("%c(%P)", 0, (1, -4, ", ", 100)), node)
        self.prec = p
        node.kind = "async_call"
        self.prune()

    self.n_async_call = n_async_call

    def n_attribute37(node):
        expr = node[0]
        assert expr == "expr"
        if expr[0] == "LOAD_CONST":
            # FIXME: I didn't record which constants parenthesis is
            # necessary. However, I suspect that we could further
            # refine this by looking at operator precedence and
            # eval'ing the constant value (pattr) and comparing with
            # the type of the constant.
            node.kind = "attribute_w_parens"
        self.default(node)

    self.n_attribute37 = n_attribute37

    def n_build_list_unpack(node):
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
        last_was_star = self.f.getvalue().endswith("*")

        if lastnodetype.startswith("BUILD_LIST"):
            self.write("[")
            endchar = "]"
        else:
            endchar = ""

        flat_elems = flatten_list(node)

        self.indent_more(INDENT_PER_LEVEL)
        sep = ""
        for elem in flat_elems:
            if elem in ("ROT_THREE", "EXTENDED_ARG"):
                continue
            assert elem == "expr"
            line_number = self.line_number
            use_star = True
            value = self.traverse(elem)
            if value.startswith("("):
                assert value.endswith(")")
                use_star = False
                value = value[1:-1].rstrip(
                    " "
                )  # Remove starting '(' and trailing ')' and additional spaces
                if value == "":
                    pass
                else:
                    if value.endswith(","):  # if args has only one item
                        value = value[:-1]
            if line_number != self.line_number:
                sep += "\n" + self.indent + INDENT_PER_LEVEL[:-1]
            else:
                if sep != "":
                    sep += " "
            if not last_was_star and use_star:
                sep += "*"
                pass
            else:
                last_was_star = False
            self.write(sep, value)
            sep = ","
        self.write(endchar)
        self.indent_less(INDENT_PER_LEVEL)

        self.prec = p
        self.prune()
        return

    self.n_build_list_unpack = n_build_list_unpack

    def n_c_with(node):
        if len(node) == 1 and node[0] == "with":
            node = node[0]
        else:
            node.kind = "with"
        self.default(node)

    self.n_c_with = n_c_with

    def n_c_except_suite(node):
        node_len = len(node)
        if node_len == 1 and node[0] in ("except_suite", "c_returns"):
            node = node[0]
            self.default(node)
        elif node[1] in ("c_suite_stmts", "c_except_suite"):
            node = node[1][0]
            template = ("%+%c%-", 0)
            self.template_engine(template, node)
            self.prune()

    self.n_c_except_suite = n_c_except_suite

    self.n_c_with = n_c_with

    def n_call(node):
        p = self.prec
        self.prec = 100
        mapping = self._get_mapping(node)
        table = mapping[0]
        key = node
        for i in mapping[1:]:
            key = key[i]
            pass
        opname = key.kind
        if opname.startswith("CALL_FUNCTION_VAR_KW"):
            # Python 3.5 changes the stack position of
            # *args: kwargs come after *args whereas
            # in earlier Pythons, *args is at the end
            # which simplifies things from our
            # perspective.  Python 3.6+ replaces
            # CALL_FUNCTION_VAR_KW with
            # CALL_FUNCTION_EX We will just swap the
            # order to make it look like earlier
            # Python 3.
            entry = table[key.kind]
            kwarg_pos = entry[2][1]
            args_pos = kwarg_pos - 1
            # Put last node[args_pos] after subsequent kwargs
            while node[kwarg_pos] == "kwarg" and kwarg_pos < len(node):
                # swap node[args_pos] with node[kwargs_pos]
                node[kwarg_pos], node[args_pos] = node[args_pos], node[kwarg_pos]
                args_pos = kwarg_pos
                kwarg_pos += 1
        elif opname.startswith("CALL_FUNCTION_VAR"):
            # CALL_FUNCTION_VAR's top element of the stack contains
            # the variable argument list, then comes
            # annotation args, then keyword args.
            # In the most least-top-most stack entry, but position 1
            # in node order, the positional args.
            argc = node[-1].attr
            nargs = argc & 0xFF
            kwargs = (argc >> 8) & 0xFF
            # FIXME: handle annotation args
            if nargs > 0:
                template = ("%c(%P, ", 0, (1, nargs + 1, ", ", 100))
            else:
                template = ("%c(", 0)
            self.template_engine(template, node)

            args_node = node[-2]
            if args_node in ("pos_arg", "expr"):
                args_node = args_node[0]
            if args_node == "build_list_unpack":
                template = ("*%P)", (0, len(args_node) - 1, ", *", 100))
                self.template_engine(template, args_node)
            else:
                if len(node) - nargs > 3:
                    template = (
                        "*%c, %P)",
                        nargs + 1,
                        (nargs + kwargs + 1, -1, ", ", 100),
                    )
                else:
                    template = ("*%c)", nargs + 1)
                self.template_engine(template, node)
            self.prec = p
            self.prune()
        elif (
            opname.startswith("CALL_FUNCTION_1")
            and opname == "CALL_FUNCTION_1"
            or not re.match(r"\d", opname[-1])
        ):
            template = "(%c)(%p)" if node[0][0] == "lambda_body" else "%c(%p)"
            self.template_engine(
                (template, (0, "expr"), (1, PRECEDENCE["yield"] - 1)), node
            )
            self.prec = p
            self.prune()
        else:
            gen_function_parens_adjust(key, node)

        self.prec = p
        self.default(node)

    self.n_call = n_call

    def n_compare_chained(node):
        if node[0] in (
            "c_compare_chained37",
            "c_compare_chained37_false",
            "compare_chained37",
            "compare_chained37_false",
        ):
            self.default(node[0])
        else:
            self.default(node)

    self.n_compare_chained = self.n_c_compare_chained = n_compare_chained

    def n_importlist37(node):
        if len(node) == 1:
            self.default(node)
            return
        n = len(node) - 1
        for i in range(n, -1, -1):
            if node[i] != "ROT_TWO":
                break
        self.template_engine(("%C", (0, i + 1, ", ")), node)
        self.prune()
        return

    self.n_importlist37 = n_importlist37

    def n_list_comp_async(node):
        self.write("[")
        if node[0].kind == "load_closure":
            self.listcomp_closure3(node)
        else:
            self.comprehension_walk_newer(node, iter_index=3, code_index=0)
        self.write("]")
        self.prune()

    self.n_list_comp_async = n_list_comp_async

    # FIXME: The following adjusts I guess a bug in the parser.
    # It might be as simple as renaming grammar symbol "testtrue" to "testtrue_or_false"
    # and then keeping this as is with the name change.
    # Fixing in the parsing by inspection is harder than doing it here.
    def n_testtrue(node):
        compare_chained37 = node[0]
        if (
            compare_chained37 == "compare_chained37"
            and compare_chained37[1] == "compare_chained1b_37"
        ):
            compare_chained1b_37 = compare_chained37[1]
            if (
                len(compare_chained1b_37) > 2
                and compare_chained1b_37[-2] == "JUMP_FORWARD"
            ):
                node.kind = "testfalse"
                pass
            pass
        self.default(node)
        return

    self.n_testtrue = n_testtrue
