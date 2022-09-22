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
"""Isolate Python 3.5 version-specific semantic actions here.
"""

from xdis import co_flags_is_async, iscode
from uncompyle6.semantics.consts import (
    INDENT_PER_LEVEL,
    PRECEDENCE,
    TABLE_DIRECT,
)

from uncompyle6.semantics.helper import flatten_list, gen_function_parens_adjust


#######################
# Python 3.5+ Changes #
#######################
def customize_for_version35(self, version):
    # fmt: off
    TABLE_DIRECT.update(
        {
            # nested await expressions like:
            #   return await (await bar())
            # need parenthesis.
            "await_expr": ("await %p", (0, PRECEDENCE["await_expr"] - 1)),

            "await_stmt": ("%|%c\n", 0),
            "async_for_stmt": (
                "%|async for %c in %c:\n%+%|%c%-\n\n",
                (9, "store"),
                (1, "expr"),
                (25, ("for_block", "pass")),
            ),
            "async_forelse_stmt": (
                "%|async for %c in %c:\n%+%c%-%|else:\n%+%c%-\n\n",
                (9, "store"),
                (1, "expr"),
                (25, "for_block"),
                (-2, "else_suite"),
            ),
            "async_with_stmt": (
                "%|async with %c:\n%+%c%-",
                (0, "expr"),
                3
            ),
            "async_with_as_stmt": (
                "%|async with %c as %c:\n%+%c%-",
                (0, "expr"),
                (2, "store"),
                3,
            ),
            "dict_unpack": ("{**%C}", (0, -1, ", **")),
            # "unmapexpr":	       ( "{**%c}", 0), # done by n_unmapexpr
        }
    )

    # fmt: on

    def async_call(node):
        self.f.write("async ")
        node.kind == "call"
        p = self.prec
        self.prec = 80
        self.template_engine(("%c(%P)", 0, (1, -4, ", ", 100)), node)
        self.prec = p
        node.kind == "async_call"
        self.prune()

    self.n_async_call = async_call

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
                )  # Remove starting "(" and trailing ")" and additional spaces
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

    def n_call(node):
        p = self.prec
        self.prec = 100
        mapping = self._get_mapping(node)
        table = mapping[0]
        key = node
        for i in mapping[1:]:
            key = key[i]
            pass
        if key.kind.startswith("CALL_FUNCTION_VAR_KW"):
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
        elif key.kind.startswith("CALL_FUNCTION_VAR"):
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
                    template = ("*%c, %P)", nargs + 1, (nargs + kwargs + 1, -1, ", ", 100))
                else:
                    template = ("*%c)", nargs + 1)
                self.template_engine(template, node)
            self.prec = p
            self.prune()
        else:
            gen_function_parens_adjust(key, node)

        self.prec = 100
        self.default(node)

    self.n_call = n_call

    def is_async_fn(node):
        code_node = node[0][0]
        for n in node[0]:
            if hasattr(n, "attr") and iscode(n.attr):
                code_node = n
                break
            pass
        pass

        is_code = hasattr(code_node, "attr") and iscode(code_node.attr)
        return is_code and co_flags_is_async(code_node.attr.co_flags)

    def n_function_def(node):
        if is_async_fn(node):
            self.template_engine(("\n\n%|async def %c\n", -2), node)
        else:
            self.default(node)
        self.prune()

    self.n_function_def = n_function_def

    def n_mkfuncdeco0(node):
        if is_async_fn(node):
            self.template_engine(("%|async def %c\n", 0), node)
        else:
            self.default(node)
        self.prune()

    self.n_mkfuncdeco0 = n_mkfuncdeco0

    def unmapexpr(node):
        last_n = node[0][-1]
        for n in node[0]:
            self.preorder(n)
            if n != last_n:
                self.f.write(", **")
                pass
            pass
        self.prune()
        pass

    self.n_unmapexpr = unmapexpr

    # FIXME: start here
    def n_list_unpack(node):
        """
        prettyprint an unpacked list or tuple
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

        elif lastnodetype.startswith("BUILD_SET"):
            self.write("{")
            endchar = "}"
        elif lastnodetype.startswith("BUILD_MAP_UNPACK"):
            self.write("{*")
            endchar = "}"
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
            if elem[0] == "tuple":
                assert value[0] == "("
                assert value[-1] == ")"
                value = value[1:-1]
                if value[-1] == ",":
                    # singleton tuple
                    value = value[:-1]
            else:
                value = "*" + value
            if line_number != self.line_number:
                sep += "\n" + self.indent + INDENT_PER_LEVEL[:-1]
            else:
                if sep != "":
                    sep += " "
            if not last_was_star:
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

    self.n_tuple_unpack = n_list_unpack
