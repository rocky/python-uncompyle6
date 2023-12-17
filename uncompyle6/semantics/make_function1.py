#  Copyright (c) 2015-2023 by Rocky Bernstein
#  Copyright (c) 2000-2002 by hartmut Goebel <h.goebel@crazy-compilers.com>
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
All the crazy things we have to do to handle Python functions in Python before 3.0.
The saga of changes continues in 3.0 and above and in other files.
"""
from typing import List, Tuple
from uncompyle6.scanner import Code
from uncompyle6.semantics.parser_error import ParserError
from uncompyle6.parser import ParserError as ParserError2
from uncompyle6.semantics.helper import (
    print_docstring,
    find_all_globals,
    find_globals_and_nonlocals,
    find_none,
)
from xdis import iscode

def make_function1(self, node, is_lambda, nested=1, code_node=None):
    """
    Dump function definition, doc string, and function body.
    This code is specialied for Python 2.
    """

    def build_param(tree, param_names: List[str]) -> Tuple[bool, List[str]]:
        """build parameters:
            - handle defaults
            - handle format tuple parameters
        """
        # if formal parameter is a tuple, the parameter name
        # starts with a dot (eg. '.1', '.2')
        args = tree[0]
        del tree[0]
        params = []
        assert args.kind in ("star_args", "args", "varargs")
        has_star_arg = args.kind in ("star_args", "varargs")
        args_store = args[2]
        if args_store == "args_store":
            for arg in args_store:
                params.append(param_names[arg.attr])
        return has_star_arg, params

    # MAKE_FUNCTION_... or MAKE_CLOSURE_...
    assert node[-1].kind.startswith("BUILD_")

    defparams = []
    # args_node = node[-1]
    # if isinstance(args_node.attr, tuple):
    #     # positional args are after kwargs
    #     defparams = node[1 : args_node.attr[0] + 1]
    #     pos_args, kw_args, annotate_argc = args_node.attr
    # else:
    #     defparams = node[: args_node.attr]
    #     kw_args = 0
    #     pass

    lambda_index = None

    if lambda_index and is_lambda and iscode(node[lambda_index].attr):
        assert node[lambda_index].kind == "LOAD_LAMBDA"
        code = node[lambda_index].attr
    else:
        code = code_node.attr

    assert iscode(code)
    code = Code(code, self.scanner, self.currentclass)

    # add defaults values to parameter names
    argc = code.co_argcount
    paramnames = list(code.co_varnames[:argc])

    # defaults are for last n parameters, thus reverse
    paramnames.reverse()
    defparams.reverse()

    try:
        tree = self.build_ast(
            code._tokens,
            code._customize,
            code,
            is_lambda=is_lambda,
            noneInNames=("None" in code.co_names),
        )
    except (ParserError, ParserError2) as p:
        self.write(str(p))
        if not self.tolerate_errors:
            self.ERROR = p
        return

    indent = self.indent

    # build parameters
    has_star_arg, params = build_param(tree, code.co_names)

    if has_star_arg:
        params[-1] = "*" + params[-1]

    # dump parameter list (with default values)
    if is_lambda:
        self.write("lambda ", ", ".join(params))
        # If the last statement is None (which is the
        # same thing as "return None" in a lambda) and the
        # next to last statement is a "yield". Then we want to
        # drop the (return) None since that was just put there
        # to have something to after the yield finishes.
        # FIXME: this is a bit hoaky and not general
        if (
            len(tree) > 1
            and self.traverse(tree[-1]) == "None"
            and self.traverse(tree[-2]).strip().startswith("yield")
        ):
            del tree[-1]
            # Now pick out the expr part of the last statement
            tree_expr = tree[-1]
            while tree_expr.kind != "expr":
                tree_expr = tree_expr[0]
            tree[-1] = tree_expr
            pass
    else:
        self.write("(", ", ".join(params))

    # if kw_args > 0:
    #     if not (4 & code.co_flags):
    #         if argc > 0:
    #             self.write(", *, ")
    #         else:
    #             self.write("*, ")
    #         pass
    #     else:
    #         self.write(", ")

    #     for n in node:
    #         if n == "pos_arg":
    #             continue
    #         else:
    #             self.preorder(n)
    #         break
    #     pass

    # if code_has_star_star_arg(code):
    #     if argc > 0:
    #         self.write(", ")
    #     self.write("**%s" % code.co_varnames[argc + kw_pairs])

    if is_lambda:
        self.write(": ")
    else:
        self.println("):")

    if (
        len(code.co_consts) > 0 and code.co_consts[0] is not None and not is_lambda
    ):  # ugly
        # docstring exists, dump it
        print_docstring(self, indent, code.co_consts[0])

    if not is_lambda:
        assert tree == "stmts"

    all_globals = find_all_globals(tree, set())

    globals, nonlocals = find_globals_and_nonlocals(
        tree, set(), set(), code, self.version
    )

    # Python 1 doesn't support the "nonlocal" statement

    for g in sorted((all_globals & self.mod_globs) | globals):
        self.println(self.indent, "global ", g)
    self.mod_globs -= all_globals
    has_none = "None" in code.co_names
    rn = has_none and not find_none(tree)
    tree.code = code
    self.gen_source(
        tree, code.co_name, code._customize, is_lambda=is_lambda, returnNone=rn
    )

    code._tokens = None # save memory
    code._customize = None  # save memory
