#  Copyright (c) 2015-2021, 2024 by Rocky Bernstein
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
All the crazy things we have to do to handle Python functions in 3.0-3.5 or so.
The saga of changes before and after is in other files.
"""
from xdis import CO_GENERATOR, code_has_star_arg, code_has_star_star_arg, iscode

from uncompyle6.parser import ParserError as ParserError2
from uncompyle6.parsers.treenode import SyntaxTree
from uncompyle6.scanner import Code
from uncompyle6.semantics.helper import (
    find_all_globals,
    find_globals_and_nonlocals,
    find_none,
    print_docstring,
)
from uncompyle6.semantics.parser_error import ParserError
from uncompyle6.show import maybe_show_tree_param_default

# FIXME: DRY the below code...


def make_function3_annotate(
    self, node, is_lambda, nested=1, code_node=None, annotate_last=-1
):
    """
    Dump function definition, doc string, and function
    body. This code is specialized for Python 3"""

    def build_param(ast, name, default):
        """build parameters:
        - handle defaults
        - handle format tuple parameters
        """
        if default:
            value = self.traverse(default, indent="")
            maybe_show_tree_param_default(self, name, value)
            result = "%s=%s" % (name, value)
            if result[-2:] == "= ":  # default was 'LOAD_CONST None'
                result += "None"
            return result
        else:
            return name

    # MAKE_FUNCTION_... or MAKE_CLOSURE_...
    assert node[-1].kind.startswith("MAKE_")

    annotate_tuple = None
    for annotate_last in range(len(node) - 1, -1, -1):
        if node[annotate_last] == "annotate_tuple":
            annotate_tuple = node[annotate_last]
            break
    annotate_args = {}

    if (
        annotate_tuple == "annotate_tuple"
        and annotate_tuple[0] in ("LOAD_CONST", "LOAD_NAME")
        and isinstance(annotate_tuple[0].attr, tuple)
    ):
        annotate_tup = annotate_tuple[0].attr
        i = -1
        j = annotate_last - 1
        l = -len(node)
        while j >= l and node[j].kind in ("annotate_arg", "annotate_tuple"):
            annotate_args[annotate_tup[i]] = node[j][0]
            i -= 1
            j -= 1

    args_node = node[-1]
    if isinstance(args_node.attr, tuple):
        # positional args are before kwargs
        defparams = node[: args_node.attr[0]]
        pos_args, kw_args, annotate_argc = args_node.attr
    else:
        defparams = node[: args_node.attr]
        kw_args = 0
        pass

    annotate_dict = {}

    for name in annotate_args.keys():
        n = self.traverse(annotate_args[name], indent="")
        annotate_dict[name] = n

    if (3, 0) <= self.version < (3, 3):
        lambda_index = -2
    elif self.version < (3, 4):
        lambda_index = -3
    else:
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
    kwonlyargcount = code.co_kwonlyargcount

    paramnames = list(code.co_varnames[:argc])
    if kwonlyargcount > 0:
        kwargs = list(code.co_varnames[argc : argc + kwonlyargcount])

    try:
        ast = self.build_ast(
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

    if is_lambda:
        self.write("lambda ")
    else:
        self.write("(")

    last_line = self.f.getvalue().split("\n")[-1]
    l = len(last_line)
    indent = " " * l
    line_number = self.line_number

    i = len(paramnames) - len(defparams)
    suffix = ""

    for param in paramnames[:i]:
        self.write(suffix, param)
        suffix = ", "
        if param in annotate_dict:
            self.write(": %s" % annotate_dict[param])
            if line_number != self.line_number:
                suffix = ",\n" + indent
                line_number = self.line_number
            # value, string = annotate_args[param]
            # if string:
            #     self.write(': "%s"' % value)
            # else:
            #     self.write(': %s' % value)

    suffix = ", " if i > 0 else ""
    for n in node:
        if n == "pos_arg":
            self.write(suffix)
            param = paramnames[i]
            self.write(param)
            if param in annotate_args:
                aa = annotate_args[param]
                if isinstance(aa, tuple):
                    aa = aa[0]
                    self.write(': "%s"' % aa)
                elif isinstance(aa, SyntaxTree):
                    self.write(": ")
                    self.preorder(aa)

            self.write("=")
            i += 1
            self.preorder(n)
            if line_number != self.line_number:
                suffix = ",\n" + indent
                line_number = self.line_number
            else:
                suffix = ", "

    if code_has_star_arg(code):
        star_arg = code.co_varnames[argc + kwonlyargcount]
        if annotate_dict and star_arg in annotate_dict:
            self.write(suffix, "*%s: %s" % (star_arg, annotate_dict[star_arg]))
        else:
            self.write(suffix, "*%s" % star_arg)
        argc += 1

    # self.println(indent, '#flags:\t', int(code.co_flags))
    ends_in_comma = False
    if kwonlyargcount > 0:
        if not code_has_star_arg(code):
            if argc > 0:
                self.write(", *, ")
            else:
                self.write("*, ")
            pass
            ends_in_comma = True
        else:
            if argc > 0:
                self.write(", ")
                ends_in_comma = True

        kw_args = [None] * kwonlyargcount

        for n in node:
            if n == "kwargs":
                n = n[0]
            if n == "kwarg":
                name = eval(n[0].pattr)
                idx = kwargs.index(name)
                default = self.traverse(n[1], indent="")
                if annotate_dict and name in annotate_dict:
                    kw_args[idx] = "%s: %s=%s" % (name, annotate_dict[name], default)
                else:
                    kw_args[idx] = "%s=%s" % (name, default)
                pass
            pass

        # handling other args
        other_kw = [c == None for c in kw_args]
        for i, flag in enumerate(other_kw):
            if flag:
                n = kwargs[i]
                if n in annotate_dict:
                    kw_args[i] = "%s: %s" % (n, annotate_dict[n])
                else:
                    kw_args[i] = "%s" % n

        self.write(", ".join(kw_args))
        ends_in_comma = False

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
        if "return" in annotate_tuple[0].attr:
            if (line_number != self.line_number) and not no_paramnames:
                self.write("\n" + indent)
                line_number = self.line_number
            self.write(" -> ")
            if "return" in annotate_dict:
                self.write(annotate_dict["return"])
            else:
                # value, string = annotate_args['return']
                # if string:
                #     self.write(' -> "%s"' % value)
                # else:
                #     self.write(' -> %s' % value)
                self.preorder(node[annotate_last - 1])

        self.println(":")

    if (
        len(code.co_consts) > 0 and code.co_consts[0] is not None and not is_lambda
    ):  # ugly
        # docstring exists, dump it
        print_docstring(self, self.indent, code.co_consts[0])

    code._tokens = None  # save memory
    assert ast == "stmts"

    all_globals = find_all_globals(ast, set())
    globals, nonlocals = find_globals_and_nonlocals(
        ast, set(), set(), code, self.version
    )
    for g in sorted((all_globals & self.mod_globs) | globals):
        self.println(self.indent, "global ", g)
    for nl in sorted(nonlocals):
        self.println(self.indent, "nonlocal ", nl)
    self.mod_globs -= all_globals
    has_none = "None" in code.co_names
    rn = has_none and not find_none(ast)
    self.gen_source(
        ast, code.co_name, code._customize, is_lambda=is_lambda, returnNone=rn
    )
    code._tokens = code._customize = None  # save memory


def make_function3(self, node, is_lambda, nested=1, code_node=None):
    """Dump function definition, doc string, and function body in
    Python version 3.0 and above
    """

    # For Python 3.3, the evaluation stack in MAKE_FUNCTION is:

    # * default argument objects in positional order
    # * pairs of name and default argument, with the name just below
    #   the object on the stack, for keyword-only parameters
    # * parameter annotation objects
    # * a tuple listing the parameter names for the annotations
    #   (only if there are only annotation objects)
    # * the code associated with the function (at TOS1)
    # * the qualified name of the function (at TOS)

    # For Python 3.0 .. 3.2 the evaluation stack is:
    # The function object is defined to have argc default parameters,
    # which are found below TOS.
    # * first come positional args in the order they are given in the source,
    # * next come the keyword args in the order they given in the source,
    # * finally is the code associated with the function (at TOS)
    #
    # Note: There is no qualified name at TOS

    # MAKE_CLOSURE adds an additional closure slot

    # In Python 3.6 stack entries change again. I understand
    # 3.7 changes some of those changes. Yes, it is hard to follow
    # and I am sure I haven't been able to keep up.

    # Thank you, Python.

    def build_param(ast, name, default, annotation=None):
        """build parameters:
        - handle defaults
        - handle format tuple parameters
        """
        value = self.traverse(default, indent="")
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
    if (3, 0) <= self.version <= (3, 2):
        lambda_index = -2
    elif (3, 3) <= self.version:
        lambda_index = -3
    else:
        lambda_index = None

    args_node = node[-1]

    annotate_dict = {}

    # Get a list of tree nodes that constitute the values for the "default
    # parameters"; these are default values that appear before any *, and are
    # not to be confused with keyword parameters which may appear after *.
    args_attr = args_node.attr

    if isinstance(args_attr, tuple):
        if len(args_attr) == 3:
            pos_args, kw_args, annotate_argc = args_attr
        else:
            pos_args, kw_args, annotate_argc, closure = args_attr

            i = -4
            kw_pairs = 0
            if closure:
                # FIXME: fill in
                i -= 1
            if annotate_argc:
                # Turn into subroutine and DRY with other use
                annotate_node = node[i]
                if annotate_node == "expr":
                    annotate_node = annotate_node[0]
                    annotate_name_node = annotate_node[-1]
                    if annotate_node == "dict" and annotate_name_node.kind.startswith(
                        "BUILD_CONST_KEY_MAP"
                    ):
                        types = [
                            self.traverse(n, indent="") for n in annotate_node[:-2]
                        ]
                        names = annotate_node[-2].attr
                        l = len(types)
                        assert l == len(names)
                        for i in range(l):
                            annotate_dict[names[i]] = types[i]
                        pass
                    pass
                i -= 1
            if kw_args:
                kw_node = node[i]
                if kw_node == "expr":
                    kw_node = kw_node[0]
                if kw_node == "dict":
                    kw_pairs = kw_node[-1].attr

        # FIXME: there is probably a better way to classify this.
        have_kwargs = node[0].kind.startswith("kwarg") or node[0] == "no_kwargs"
        if len(node) >= 4:
            lc_index = -4
        else:
            lc_index = -3
            pass

        if len(node) > 2 and (have_kwargs or node[lc_index].kind != "load_closure"):
            # Find the index in "node" where the first default
            # parameter value is located. Note this is in contrast to
            # key-word arguments, pairs of (name, value), which appear after "*".
            # "default_values_start" is this location.
            default_values_start = 0
            if node[0] == "no_kwargs":
                default_values_start += 1

            # If in a lambda named args are a sequence of kwarg, not bundled.
            # If not in a lambda, named args are after kwargs; kwargs are bundled as one node.
            if node[default_values_start] == "kwarg":
                assert node[lambda_index] == "LOAD_LAMBDA"
                i = default_values_start
                defparams = []
                while node[i] == "kwarg":
                    defparams.append(node[i][1])
                    i += 1
            else:
                if node[default_values_start] == "kwargs":
                    default_values_start += 1
                defparams = node[
                    default_values_start : default_values_start + args_node.attr[0]
                ]
        else:
            defparams = node[: args_node.attr[0]]
            kw_args = 0
    else:
        defparams = node[: args_node.attr]
        kw_args = 0
        pass

    if lambda_index and is_lambda and iscode(node[lambda_index].attr):
        assert node[lambda_index].kind == "LOAD_LAMBDA"
        code = node[lambda_index].attr
    else:
        code = code_node.attr

    assert iscode(code)
    scanner_code = Code(code, self.scanner, self.currentclass)

    # add defaults values to parameter names
    argc = code.co_argcount
    kwonlyargcount = code.co_kwonlyargcount

    paramnames = list(scanner_code.co_varnames[:argc])
    if kwonlyargcount > 0:
        if is_lambda:
            kwargs = []
            for i in range(kwonlyargcount):
                paramnames.append(scanner_code.co_varnames[argc + i])
            pass
        else:
            kwargs = list(scanner_code.co_varnames[argc : argc + kwonlyargcount])

    # defaults are for last n parameters when not in a lambda, thus reverse
    paramnames.reverse()
    defparams.reverse()

    try:
        ast = self.build_ast(
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
                    ast, paramnames[i], defparam, annotate_dict.get(paramnames[i])
                )
            )

        for param in paramnames[i + 1 :]:
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
        if annotate_dict and star_arg in annotate_dict:
            params.append("*%s: %s" % (star_arg, annotate_dict[star_arg]))
        else:
            params.append("*%s" % star_arg)
            pass
        if is_lambda:
            params.reverse()
        if not is_lambda:
            argc += 1
        pass
    elif is_lambda and kwonlyargcount > 0:
        params.insert(0, "*")
        kwonlyargcount = 0

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
            len(ast) > 1
            and self.traverse(ast[-1]) == "None"
            and self.traverse(ast[-2]).strip().startswith("yield")
        ):
            del ast[-1]
            # Now pick out the expr part of the last statement
            ast_expr = ast[-1]
            while ast_expr.kind != "expr":
                ast_expr = ast_expr[0]
            ast[-1] = ast_expr
            pass
    else:
        # FIXME: add annotations here
        self.write("(", ", ".join(params))
    # self.println(indent, '#flags:\t', int(code.co_flags))

    # FIXME: Could we remove ends_in_comma and its tests if we just
    # created a parameter list and at the very end did a join on that?
    # Unless careful, We might lose line breaks though.
    ends_in_comma = False
    if kwonlyargcount > 0:
        if not (4 & code.co_flags):
            if argc > 0:
                self.write(", *, ")
            else:
                self.write("*, ")
            pass
            ends_in_comma = True
        else:
            if argc > 0 and node[0] != "kwarg":
                self.write(", ")
                ends_in_comma = True

        kw_args = [None] * kwonlyargcount
        if self.version <= (3, 3):
            kw_nodes = node[0]
        else:
            kw_nodes = node[args_node.attr[0]]
        if kw_nodes == "kwargs":
            for n in kw_nodes:
                name = eval(n[0].pattr)
                default = self.traverse(n[1], indent="")
                idx = kwargs.index(name)
                kw_args[idx] = "%s=%s" % (name, default)
                pass
            pass

        # FIXME: something weird is going on and the below
        # might not be right. On 3.4 kw_nodes != "kwarg"
        # because of some sort of type mismatch. I think
        # the test is for versions earlier than 3.3
        # on 3.5 if we have "kwarg" we still want to do this.
        # Perhaps we should be testing that kw_nodes is iterable?
        if kw_nodes != "kwarg" or self.version == 3.5:
            other_kw = [c == None for c in kw_args]

            for i, flag in enumerate(other_kw):
                if flag:
                    if i < len(kwargs):
                        kw_args[i] = "%s" % kwargs[i]
                    else:
                        del kw_args[i]
                    pass

            self.write(", ".join(kw_args))
            ends_in_comma = False
            pass

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

    if (
        len(code.co_consts) > 0 and code.co_consts[0] is not None and not is_lambda
    ):  # ugly
        # docstring exists, dump it
        print_docstring(self, self.indent, code.co_consts[0])

    assert ast == "stmts"

    all_globals = find_all_globals(ast, set())
    globals, nonlocals = find_globals_and_nonlocals(
        ast, set(), set(), code, self.version
    )

    for g in sorted((all_globals & self.mod_globs) | globals):
        self.println(self.indent, "global ", g)

    for nl in sorted(nonlocals):
        self.println(self.indent, "nonlocal ", nl)

    self.mod_globs -= all_globals
    has_none = "None" in code.co_names
    rn = has_none and not find_none(ast)
    self.gen_source(
        ast,
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
    # Python 3.x's test_generator.py test program.
    if not is_lambda and code.co_flags & CO_GENERATOR:
        need_bogus_yield = True
        for token in scanner_code._tokens:
            if token in ("YIELD_VALUE", "YIELD_FROM"):
                need_bogus_yield = False
                break
            pass
        if need_bogus_yield:
            self.template_engine(("%|if False:\n%+%|yield None%-",), node)

    scanner_code._tokens = None  # save memory
    scanner_code._customize = None  # save memory
