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
"""
All the crazy things we have to do to handle Python functions in 3.6 and above.
The saga of changes before 3.6 is in other files.
"""
from xdis import (
    iscode,
    code_has_star_arg,
    code_has_star_star_arg,
    CO_GENERATOR,
    CO_ASYNC_GENERATOR,
)
from uncompyle6.scanner import Code
from uncompyle6.semantics.parser_error import ParserError
from uncompyle6.parser import ParserError as ParserError2
from uncompyle6.semantics.helper import (
    find_all_globals,
    find_globals_and_nonlocals,
    find_none,
)

from uncompyle6.show import maybe_show_tree_param_default


def make_function36(self, node, is_lambda, nested=1, code_node=None):
    """Dump function definition, doc string, and function body in
    Python version 3.6 and above.
    """

    # MAKE_CLOSURE adds a closure slot

    # In Python 3.6 and above stack change again. I understand
    # 3.7 changes some of those changes, although I don't
    # see it in this code yet. Yes, it is hard to follow,
    # and I am sure I haven't been able to keep up.

    # Thank you, Python.

    def build_param(ast, name, default, annotation=None):
        """build parameters:
        - handle defaults
        - handle format tuple parameters
        """
        value = default
        maybe_show_tree_param_default(self.showast, name, value)
        if annotation:
            result = "%s: %s=%s" % (name, annotation, value)
        else:
            result = "%s=%s" % (name, value)

        # The below can probably be removed. This is probably
        # a holdover from days when LOAD_CONST erroneously
        # didn't handle LOAD_CONST None properly
        if result[-2:] == "= ":  # default was 'LOAD_CONST None'
            result += "None"

        return result

    # MAKE_FUNCTION_... or MAKE_CLOSURE_...
    assert node[-1].kind.startswith("MAKE_")

    # Python 3.3+ adds a qualified name at TOS (-1)
    # moving down the LOAD_LAMBDA instruction
    lambda_index = -3

    args_node = node[-1]

    annotate_dict = {}

    # Get a list of tree nodes that constitute the values for the "default
    # parameters"; these are default values that appear before any *, and are
    # not to be confused with keyword parameters which may appear after *.
    args_attr = args_node.attr

    if len(args_attr) == 3:
        _, kw_args, annotate_argc = args_attr
    else:
        _, kw_args, annotate_argc, closure = args_attr

    if node[-2] != "docstring":
        i = -4
    else:
        i = -5

    if annotate_argc:
        # Turn into subroutine and DRY with other use
        annotate_node = node[i]
        if annotate_node == "expr":
            annotate_node = annotate_node[0]
            annotate_name_node = annotate_node[-1]
            if annotate_node == "dict" and annotate_name_node.kind.startswith(
                "BUILD_CONST_KEY_MAP"
            ):
                types = [self.traverse(n, indent="") for n in annotate_node[:-2]]
                names = annotate_node[-2].attr
                length = len(types)
                assert length == len(names)
                for i in range(length):
                    annotate_dict[names[i]] = types[i]
                pass
            pass
        i -= 1

    if closure:
        # FIXME: fill in
        # annotate = node[i]
        i -= 1

    defparams = []
    # FIXME: DRY with code below
    default, kw_args, annotate_argc = args_node.attr[0:3]
    if default:
        expr_node = node[0]
        if node[0] == "pos_arg":
            expr_node = expr_node[0]
        assert expr_node == "expr", "expecting mkfunc default node to be an expr"
        if expr_node[0] == "LOAD_CONST" and isinstance(expr_node[0].attr, tuple):
            defparams = [repr(a) for a in expr_node[0].attr]
        elif expr_node[0] in frozenset(("list", "tuple", "dict", "set")):
            defparams = [self.traverse(n, indent="") for n in expr_node[0][:-1]]
    else:
        defparams = []
    pass

    if lambda_index and is_lambda and iscode(node[lambda_index].attr):
        assert node[lambda_index].kind == "LOAD_LAMBDA"
        code = node[lambda_index].attr
    else:
        code = code_node.attr

    assert iscode(code)
    debug_opts = self.debug_opts["asm"] if self.debug_opts else None
    scanner_code = Code(code, self.scanner, self.currentclass, debug_opts)

    # add defaults values to parameter names
    argc = code.co_argcount
    kwonlyargcount = code.co_kwonlyargcount

    paramnames = list(scanner_code.co_varnames[:argc])
    kwargs = list(scanner_code.co_varnames[argc: argc + kwonlyargcount])

    paramnames.reverse()
    defparams.reverse()

    try:
        tree = self.build_ast(
            scanner_code._tokens,
            scanner_code._customize,
            scanner_code,
            is_lambda=is_lambda,
            noneInNames=("None" in code.co_names),
        )
    except (ParserError, ParserError2) as p:
        self.write(str(p))
        if not self.tolerate_errors:
            self.ERROR = p
        return

    i = len(paramnames) - len(defparams)

    # build parameters
    params = []
    if defparams:
        for i, defparam in enumerate(defparams):
            params.append(
                build_param(
                    tree, paramnames[i], defparam, annotate_dict.get(paramnames[i])
                )
            )

        for param in paramnames[i + 1:]:
            if param in annotate_dict:
                params.append("%s: %s" % (param, annotate_dict[param]))
            else:
                params.append(param)
    else:
        for param in paramnames:
            if param in annotate_dict:
                params.append("%s: %s" % (param, annotate_dict[param]))
            else:
                params.append(param)

    params.reverse()  # back to correct order

    if code_has_star_arg(code):
        star_arg = code.co_varnames[argc + kwonlyargcount]
        if star_arg in annotate_dict:
            params.append("*%s: %s" % (star_arg, annotate_dict[star_arg]))
        else:
            params.append("*%s" % star_arg)

        argc += 1

    # dump parameter list (with default values)
    if is_lambda:
        self.write("lambda")
        if len(params):
            self.write(" ", ", ".join(params))
        elif kwonlyargcount > 0 and not (4 & code.co_flags):
            assert argc == 0
            self.write(" ")

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
    # self.println(indent, '#flags:\t', int(code.co_flags))

    ends_in_comma = False
    if kwonlyargcount > 0:
        if not 4 & code.co_flags:
            if argc > 0:
                self.write(", *, ")
            else:
                self.write("*, ")
            pass
        else:
            if argc > 0:
                self.write(", ")

        # ann_dict = kw_dict = default_tup = None
        kw_dict = None

        fn_bits = node[-1].attr
        # Skip over:
        #  MAKE_FUNCTION,
        #  optional docstring
        #  LOAD_CONST qualified name,
        #  LOAD_CONST code object
        index = -5 if node[-2] == "docstring" else -4
        if fn_bits[-1]:
            index -= 1
        if fn_bits[-2]:
            # ann_dict = node[index]
            index -= 1
        if fn_bits[-3]:
            kw_dict = node[index]
            index -= 1
        if fn_bits[-4]:
            # default_tup = node[index]
            pass

        if kw_dict == "expr":
            kw_dict = kw_dict[0]

        kw_args = [None] * kwonlyargcount

        # FIXME: handle free_tup, ann_dict, and default_tup
        if kw_dict:
            assert kw_dict == "dict"
            const_list = kw_dict[0]
            if kw_dict[0] == "const_list":
                add_consts = const_list[1]
                assert add_consts == "add_consts"
                names = add_consts[-1].attr
                defaults = [v.pattr for v in add_consts[:-1]]
            else:
                defaults = [self.traverse(n, indent="") for n in kw_dict[:-2]]
                names = eval(self.traverse(kw_dict[-2]))

            assert len(defaults) == len(names)
            # FIXME: possibly handle line breaks
            for i, n in enumerate(names):
                idx = kwargs.index(n)
                if annotate_dict and n in annotate_dict:
                    t = "%s: %s=%s" % (n, annotate_dict[n], defaults[i])
                else:
                    t = "%s=%s" % (n, defaults[i])
                kw_args[idx] = t
                pass
            pass
        # handle others
        other_kw = [c is None for c in kw_args]

        for i, flag in enumerate(other_kw):
            if flag:
                n = kwargs[i]
                if n in annotate_dict:
                    kw_args[i] = "%s: %s" % (n, annotate_dict[n])
                else:
                    kw_args[i] = "%s" % n

        self.write(", ".join(kw_args))
        ends_in_comma = False
        pass
    else:
        if argc == 0:
            ends_in_comma = True

    if code_has_star_star_arg(code):
        if not ends_in_comma:
            self.write(", ")
        star_star_arg = code.co_varnames[argc + kwonlyargcount]
        if annotate_dict and star_star_arg in annotate_dict:
            self.write("**%s: %s" % (star_star_arg, annotate_dict[star_star_arg]))
        else:
            self.write("**%s" % star_star_arg)

    if is_lambda:
        self.write(": ")
    else:
        self.write(")")
        if annotate_dict and "return" in annotate_dict:
            self.write(" -> %s" % annotate_dict["return"])
        self.println(":")

    if node[-2] == "docstring" and not is_lambda:
        # docstring exists, dump it
        self.println(self.traverse(node[-2]))

    assert tree in ("stmts", "lambda_start")

    all_globals = find_all_globals(tree, set())
    globals, nonlocals = find_globals_and_nonlocals(
        tree, set(), set(), code, self.version
    )

    for g in sorted((all_globals & self.mod_globs) | globals):
        self.println(self.indent, "global ", g)

    for nl in sorted(nonlocals):
        self.println(self.indent, "nonlocal ", nl)

    self.mod_globs -= all_globals
    has_none = "None" in code.co_names
    rn = has_none and not find_none(tree)
    self.gen_source(
        tree,
        code.co_name,
        scanner_code._customize,
        is_lambda=is_lambda,
        returnNone=rn,
        debug_opts=self.debug_opts,
    )

    # In obscure cases, a function may be a generator but the "yield"
    # was optimized away. Here, we need to put in unreachable code to
    # add in "yield" just so that the compiler will mark
    # the GENERATOR bit of the function. See for example
    # Python 3.x's test_connection.py and test_contexlib_async test programs.
    if not is_lambda and code.co_flags & (CO_GENERATOR | CO_ASYNC_GENERATOR):
        need_bogus_yield = True
        for token in scanner_code._tokens:
            if token == "YIELD_VALUE":
                need_bogus_yield = False
                break
            pass
        if need_bogus_yield:
            self.template_engine(("%|if False:\n%+%|yield None%-",), node)

    scanner_code._tokens = None  # save memory
    scanner_code._customize = None  # save memory
