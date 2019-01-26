#  Copyright (c) 2015-2018 by Rocky Bernstein
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
All the crazy things we have to do to handle Python functions
"""
from xdis.code import iscode, code_has_star_arg, code_has_star_star_arg
from uncompyle6.scanner import Code
from uncompyle6.parsers.treenode import SyntaxTree
from uncompyle6 import PYTHON3
from uncompyle6.semantics.parser_error import ParserError
from uncompyle6.parser import ParserError as ParserError2
from uncompyle6.semantics.helper import (
    print_docstring, find_all_globals, find_globals_and_nonlocals, find_none
    )

if PYTHON3:
    from itertools import zip_longest
else:
    from itertools import izip_longest as zip_longest

from uncompyle6.show import maybe_show_tree_param_default

# FIXME: DRY the below code...

def make_function3_annotate(self, node, is_lambda, nested=1,
                            code_node=None, annotate_last=-1):
    """
    Dump function defintion, doc string, and function
    body. This code is specialized for Python 3"""

    def build_param(ast, name, default):
        """build parameters:
            - handle defaults
            - handle format tuple parameters
        """
        if default:
            value = self.traverse(default, indent='')
            maybe_show_tree_param_default(self, name, value)
            result = '%s=%s' % (name,  value)
            if result[-2:] == '= ':	# default was 'LOAD_CONST None'
                result += 'None'
            return result
        else:
            return name

    # MAKE_FUNCTION_... or MAKE_CLOSURE_...
    assert node[-1].kind.startswith('MAKE_')

    annotate_tuple = None
    for annotate_last in range(len(node)-1, -1, -1):
        if node[annotate_last] == 'annotate_tuple':
            annotate_tuple = node[annotate_last]
            break
    annotate_args = {}

    if (annotate_tuple == 'annotate_tuple'
        and annotate_tuple[0] in ('LOAD_CONST', 'LOAD_NAME')
        and isinstance(annotate_tuple[0].attr, tuple)):
        annotate_tup = annotate_tuple[0].attr
        i = -1
        j = annotate_last-1
        l = -len(node)
        while j >= l and node[j].kind in ('annotate_arg' 'annotate_tuple'):
            annotate_args[annotate_tup[i]] = node[j][0]
            i -= 1
            j -= 1

    args_node = node[-1]
    if isinstance(args_node.attr, tuple):
        # positional args are before kwargs
        defparams = node[:args_node.attr[0]]
        pos_args, kw_args, annotate_argc  = args_node.attr
        if 'return' in annotate_args.keys():
            annotate_argc = len(annotate_args) - 1
    else:
        defparams = node[:args_node.attr]
        kw_args  = 0
        annotate_argc = 0
        pass

    if 3.0 <= self.version <= 3.2:
        lambda_index = -2
    elif 3.03 <= self.version:
        lambda_index = -3
    else:
        lambda_index = None

    if lambda_index and is_lambda and iscode(node[lambda_index].attr):
        assert node[lambda_index].kind == 'LOAD_LAMBDA'
        code = node[lambda_index].attr
    else:
        code = code_node.attr

    assert iscode(code)
    code = Code(code, self.scanner, self.currentclass)

    # add defaults values to parameter names
    argc = code.co_argcount
    paramnames = list(code.co_varnames[:argc])

    try:
        ast = self.build_ast(code._tokens,
                             code._customize,
                             is_lambda = is_lambda,
                             noneInNames = ('None' in code.co_names))
    except (ParserError, ParserError2) as p:
        self.write(str(p))
        if not self.tolerate_errors:
            self.ERROR = p
        return

    kw_pairs = args_node.attr[1]
    indent = self.indent

    if is_lambda:
        self.write("lambda ")
    else:
        self.write("(")

    last_line = self.f.getvalue().split("\n")[-1]
    l = len(last_line)
    indent = ' ' * l
    line_number = self.line_number

    if code_has_star_arg(code):
        self.write('*%s' % code.co_varnames[argc + kw_pairs])
        argc += 1

    i = len(paramnames) - len(defparams)
    suffix = ''

    no_paramnames = len(paramnames[:i]) == 0

    for param in paramnames[:i]:
        self.write(suffix, param)
        suffix = ', '
        if param in annotate_tuple[0].attr:
            p = annotate_tuple[0].attr.index(param)
            self.write(': ')
            self.preorder(node[p])
            if (line_number != self.line_number):
                suffix = ",\n" + indent
                line_number = self.line_number
            # value, string = annotate_args[param]
            # if string:
            #     self.write(': "%s"' % value)
            # else:
            #     self.write(': %s' % value)


    suffix = ', ' if i > 0 else ''
    for n in node:
        if n == 'pos_arg':
            no_paramnames = False
            self.write(suffix)
            param = paramnames[i]
            self.write(param)
            if param in annotate_args:
                aa = annotate_args[param]
                if isinstance(aa, tuple):
                    aa = aa[0]
                    self.write(': "%s"' % aa)
                elif isinstance(aa, SyntaxTree):
                    self.write(': ')
                    self.preorder(aa)

            self.write('=')
            i += 1
            self.preorder(n)
            if (line_number != self.line_number):
                suffix = ",\n" + indent
                line_number = self.line_number
            else:
                suffix = ', '


    # self.println(indent, '#flags:\t', int(code.co_flags))
    if kw_args + annotate_argc > 0:
        if no_paramnames:
            if not code_has_star_arg(code):
                if argc > 0:
                    self.write(", *, ")
                else:
                    self.write("*, ")
                pass
            else:
                self.write(", ")

            kwargs = node[0]
            last = len(kwargs)-1
            i = 0
            for n in node[0]:
                if n == 'kwarg':
                    if (line_number != self.line_number):
                        self.write("\n" + indent)
                        line_number = self.line_number
                    self.write('%s=' % n[0].pattr)
                    self.preorder(n[1])
                    if i < last:
                        self.write(', ')
                    i += 1
                    pass
                pass
            annotate_args = []
            for n in node:
                if n == 'annotate_arg':
                    annotate_args.append(n[0])
                elif n == 'annotate_tuple':
                    t = n[0].attr
                    if t[-1] == 'return':
                        t = t[0:-1]
                        annotate_args = annotate_args[:-1]
                        pass
                    last = len(annotate_args) - 1
                    for i in range(len(annotate_args)):
                        self.write("%s: " % (t[i]))
                        self.preorder(annotate_args[i])
                        if i < last:
                            self.write(', ')
                            pass
                        pass
                    break
                pass
            pass


        if code_has_star_star_arg(code):
            if argc > 0:
                self.write(', ')
            self.write('**%s' % code.co_varnames[argc + kw_pairs])

    if is_lambda:
        self.write(": ")
    else:
        self.write(')')
        if 'return' in annotate_tuple[0].attr:
            if (line_number != self.line_number) and not no_paramnames:
                self.write("\n" + indent)
                line_number = self.line_number
            self.write(' -> ')
            # value, string = annotate_args['return']
            # if string:
            #     self.write(' -> "%s"' % value)
            # else:
            #     self.write(' -> %s' % value)
            self.preorder(node[annotate_last-1])

        self.println(":")

    if (len(code.co_consts) > 0 and
        code.co_consts[0] is not None and not is_lambda): # ugly
        # docstring exists, dump it
        print_docstring(self, self.indent, code.co_consts[0])

    code._tokens = None # save memory
    assert ast == 'stmts'

    all_globals = find_all_globals(ast, set())
    globals, nonlocals = find_globals_and_nonlocals(ast, set(), set(),
                                                    code, self.version)
    for g in sorted((all_globals & self.mod_globs) | globals):
        self.println(self.indent, 'global ', g)
    for nl in sorted(nonlocals):
        self.println(self.indent, 'nonlocal ', nl)
    self.mod_globs -= all_globals
    has_none = 'None' in code.co_names
    rn = has_none and not find_none(ast)
    self.gen_source(ast, code.co_name, code._customize, is_lambda=is_lambda,
                    returnNone=rn)
    code._tokens = code._customize = None # save memory

def make_function2(self, node, is_lambda, nested=1, code_node=None):
    """
    Dump function defintion, doc string, and function body.
    This code is specialied for Python 2.
    """

    # FIXME: call make_function3 if we are self.version >= 3.0
    # and then simplify the below.

    def build_param(ast, name, default):
        """build parameters:
            - handle defaults
            - handle format tuple parameters
        """
        # if formal parameter is a tuple, the paramater name
        # starts with a dot (eg. '.1', '.2')
        if name.startswith('.'):
            # replace the name with the tuple-string
            name = self.get_tuple_parameter(ast, name)
            pass

        if default:
            value = self.traverse(default, indent='')
            maybe_show_tree_param_default(self.showast, name, value)
            result = '%s=%s' % (name,  value)
            if result[-2:] == '= ':	# default was 'LOAD_CONST None'
                result += 'None'
            return result
        else:
            return name

    # MAKE_FUNCTION_... or MAKE_CLOSURE_...
    assert node[-1].kind.startswith('MAKE_')

    args_node = node[-1]
    if isinstance(args_node.attr, tuple):
        # positional args are after kwargs
        defparams = node[1:args_node.attr[0]+1]
        pos_args, kw_args, annotate_argc  = args_node.attr
    else:
        defparams = node[:args_node.attr]
        kw_args  = 0
        pass

    lambda_index = None

    if lambda_index and is_lambda and iscode(node[lambda_index].attr):
        assert node[lambda_index].kind == 'LOAD_LAMBDA'
        code = node[lambda_index].attr
    else:
        code = code_node.attr

    assert iscode(code)
    code = Code(code, self.scanner, self.currentclass)

    # add defaults values to parameter names
    argc = code.co_argcount
    paramnames = list(code.co_varnames[:argc])

    # defaults are for last n parameters, thus reverse
    paramnames.reverse(); defparams.reverse()

    try:
        ast = self.build_ast(code._tokens,
                             code._customize,
                             is_lambda = is_lambda,
                             noneInNames = ('None' in code.co_names))
    except (ParserError, ParserError2) as p:
        self.write(str(p))
        if not self.tolerate_errors:
            self.ERROR = p
        return

    kw_pairs = 0
    indent = self.indent

    # build parameters
    params = [build_param(ast, name, default) for
              name, default in zip_longest(paramnames, defparams, fillvalue=None)]
    params.reverse() # back to correct order

    if code_has_star_arg(code):
        params.append('*%s' % code.co_varnames[argc])
        argc += 1

    # dump parameter list (with default values)
    if is_lambda:
        self.write("lambda ", ", ".join(params))
        # If the last statement is None (which is the
        # same thing as "return None" in a lambda) and the
        # next to last statement is a "yield". Then we want to
        # drop the (return) None since that was just put there
        # to have something to after the yield finishes.
        # FIXME: this is a bit hoaky and not general
        if (len(ast) > 1 and
            self.traverse(ast[-1]) == 'None' and
            self.traverse(ast[-2]).strip().startswith('yield')):
            del ast[-1]
            # Now pick out the expr part of the last statement
            ast_expr = ast[-1]
            while ast_expr.kind != 'expr':
                ast_expr = ast_expr[0]
            ast[-1] = ast_expr
            pass
    else:
        self.write("(", ", ".join(params))

    if kw_args > 0:
        if not (4 & code.co_flags):
            if argc > 0:
                self.write(", *, ")
            else:
                self.write("*, ")
            pass
        else:
            self.write(", ")

        for n in node:
            if n == 'pos_arg':
                continue
            else:
                self.preorder(n)
            break
        pass

    if code_has_star_star_arg(code):
        if argc > 0:
            self.write(', ')
        self.write('**%s' % code.co_varnames[argc + kw_pairs])

    if is_lambda:
        self.write(": ")
    else:
        self.println("):")

    if len(code.co_consts) > 0 and code.co_consts[0] is not None and not is_lambda: # ugly
        # docstring exists, dump it
        print_docstring(self, indent, code.co_consts[0])

    code._tokens = None # save memory
    if not is_lambda:
        assert ast == 'stmts'

    all_globals = find_all_globals(ast, set())

    globals, nonlocals = find_globals_and_nonlocals(ast, set(), set(),
                                                    code, self.version)

    # Python 2 doesn't support the "nonlocal" statement
    assert self.version >= 3.0 or not nonlocals

    for g in sorted((all_globals & self.mod_globs) | globals):
        self.println(self.indent, 'global ', g)
    self.mod_globs -= all_globals
    has_none = 'None' in code.co_names
    rn = has_none and not find_none(ast)
    self.gen_source(ast, code.co_name, code._customize, is_lambda=is_lambda,
                    returnNone=rn)
    code._tokens = None; code._customize = None # save memory


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
    #   (only if there are ony annotation objects)
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

    def build_param(ast, name, default):
        """build parameters:
            - handle defaults
            - handle format tuple parameters
        """
        if self.version >= 3.6:
            value = default
        else:
            value = self.traverse(default, indent='')
        maybe_show_tree_param_default(self.showast, name, value)
        result = '%s=%s' % (name,  value)

        # The below can probably be removed. This is probably
        # a holdover from days when LOAD_CONST erroneously
        # didn't handle LOAD_CONST None properly
        if result[-2:] == '= ':	# default was 'LOAD_CONST None'
            result += 'None'

        return result

    # MAKE_FUNCTION_... or MAKE_CLOSURE_...
    assert node[-1].kind.startswith('MAKE_')

    # Python 3.3+ adds a qualified name at TOS (-1)
    # moving down the LOAD_LAMBDA instruction
    if 3.0 <= self.version <= 3.2:
        lambda_index = -2
    elif 3.03 <= self.version:
        lambda_index = -3
    else:
        lambda_index = None

    args_node = node[-1]

    # Get a list of tree nodes that constitute the values for the "default
    # parameters"; these are default values that appear before any *, and are
    # not to be confused with keyword parameters which may appear after *.
    if isinstance(args_node.attr, tuple):
        pos_args, kw_args, annotate_argc  = args_node.attr
        # FIXME: there is probably a better way to classify this.
        have_kwargs = node[0].kind.startswith('kwarg') or node[0] == 'no_kwargs'
        if len(node) >= 4:
            lc_index = -4
        else:
            lc_index = -3
            pass

        if (3.0 <= self.version <= 3.3 and len(node) > 2 and
                node[lambda_index] != 'LOAD_LAMBDA' and
                (have_kwargs or node[lc_index].kind != 'load_closure')):

            # Find the index in "node" where the first default
            # parameter value is located. Note this is in contrast to
            # key-word arguments, pairs of (name, value), which appear after "*".
            # "default_values_start" is this location.
            default_values_start = 0
            if node[0] == 'no_kwargs':
                default_values_start += 1
            # args are after kwargs; kwargs are bundled as one node
            if node[default_values_start] == 'kwargs':
                default_values_start += 1
            defparams = node[default_values_start:default_values_start+args_node.attr[0]]
        else:
            # args are first, before kwargs. Or there simply are no kwargs.
            defparams = node[:args_node.attr[0]]
            pass
    else:
        if self.version < 3.6:
            defparams = node[:args_node.attr]
            kw_args  = 0
        else:
            default, kw_args, annotate, closure = args_node.attr
            if default:
                expr_node = node[0]
                if node[0] == 'pos_arg':
                    expr_node = expr_node[0]
                assert expr_node == 'expr', "expecting mkfunc default node to be an expr"
                if (expr_node[0] == 'LOAD_CONST' and
                    isinstance(expr_node[0].attr, tuple)):
                    defparams = [repr(a) for a in expr_node[0].attr]
                elif expr_node[0] in frozenset(('list', 'tuple', 'dict', 'set')):
                    defparams =  [self.traverse(n, indent='') for n in expr_node[0][:-1]]
            else:
                defparams = []

            i = -4
            kw_pairs = 0
            if closure:
                # FIXME: fill in
                i -= 1
            if annotate:
                # FIXME: fill in
                i -= 1
            if kw_args:
                kw_node = node[i]
                if kw_node == 'expr':
                    kw_node = kw_node[0]
                if kw_node == 'dict':
                    kw_pairs = kw_node[-1].attr
        pass

    if lambda_index and is_lambda and iscode(node[lambda_index].attr):
        assert node[lambda_index].kind == 'LOAD_LAMBDA'
        code = node[lambda_index].attr
    else:
        code = code_node.attr

    assert iscode(code)
    scanner_code = Code(code, self.scanner, self.currentclass)

    # add defaults values to parameter names
    argc = code.co_argcount
    paramnames = list(scanner_code.co_varnames[:argc])

    # defaults are for last n parameters, thus reverse
    paramnames.reverse();
    defparams.reverse()

    try:
        ast = self.build_ast(scanner_code._tokens,
                             scanner_code._customize,
                             is_lambda = is_lambda,
                             noneInNames = ('None' in code.co_names))
    except (ParserError, ParserError2) as p:
        self.write(str(p))
        if not self.tolerate_errors:
            self.ERROR = p
        return

    if self.version >= 3.0:
        if self.version < 3.6:
            kw_pairs = args_node.attr[1]
    else:
        kw_pairs = 0

    # build parameters
    params = []
    if defparams:
        for i, defparam in enumerate(defparams):
            params.append(build_param(ast, paramnames[i], defparam))

        params += paramnames[i+1:]
    else:
        params = paramnames

    params.reverse() # back to correct order

    if code_has_star_arg(code):
        if self.version > 3.0:
            params.append('*%s' % code.co_varnames[argc + kw_pairs])
        else:
            params.append('*%s' % code.co_varnames[argc])
        argc += 1

    # dump parameter list (with default values)
    if is_lambda:
        self.write("lambda ", ", ".join(params))
        # If the last statement is None (which is the
        # same thing as "return None" in a lambda) and the
        # next to last statement is a "yield". Then we want to
        # drop the (return) None since that was just put there
        # to have something to after the yield finishes.
        # FIXME: this is a bit hoaky and not general
        if (len(ast) > 1 and
            self.traverse(ast[-1]) == 'None' and
            self.traverse(ast[-2]).strip().startswith('yield')):
            del ast[-1]
            # Now pick out the expr part of the last statement
            ast_expr = ast[-1]
            while ast_expr.kind != 'expr':
                ast_expr = ast_expr[0]
            ast[-1] = ast_expr
            pass
    else:
        self.write("(", ", ".join(params))
    # self.println(indent, '#flags:\t', int(code.co_flags))

    ends_in_comma = False
    if kw_args > 0:
        if not (4 & code.co_flags):
            if argc > 0:
                self.write(", *, ")
            else:
                self.write("*, ")
            pass
        else:
            self.write(", ")
        ends_in_comma = True

        # FIXME: this is not correct for 3.5. or 3.6 (which works different)
        # and 3.7?
        if 3.0 <= self.version <= 3.2:
            kwargs = node[0]
            last = len(kwargs)-1
            i = 0
            for n in node[0]:
                if n == 'kwarg':
                    self.write('%s=' % n[0].pattr)
                    self.preorder(n[1])
                    if i < last:
                        self.write(', ')
                        ends_in_comma = True
                        pass
                    else:
                        ends_in_comma = False
                    pass
                i += 1
                pass
            pass
        elif self.version <= 3.5:
            # FIXME this is not qute right for 3.5
            for n in node:
                if n == 'pos_arg':
                    continue
                elif self.version >= 3.4 and not (n.kind in ('kwargs', 'no_kwargs', 'kwarg')):
                    continue
                else:
                    self.preorder(n)
                    ends_in_comma = False
                break
        elif self.version >= 3.6:
            # argc = node[-1].attr
            # co = node[-3].attr
            # argcount = co.co_argcount
            # kwonlyargcount = co.co_kwonlyargcount

            free_tup = annotate_dict = kw_dict = default_tup = None
            fn_bits = node[-1].attr
            index = -4  # Skip over:
                        #  MAKE_FUNCTION,
                        #  LOAD_CONST qualified name,
                        #  LOAD_CONST code object
            if fn_bits[-1]:
                free_tup = node[index]
                index -= 1
            if fn_bits[-2]:
                annotate_dict = node[index]
                index -= 1
            if fn_bits[-3]:
                kw_dict = node[index]
                index -= 1
            if fn_bits[-4]:
                default_tup = node[index]

            if kw_dict == 'expr':
                kw_dict = kw_dict[0]

            # FIXME: handle free_tup, annotate_dict, and default_tup
            if kw_dict:
                assert kw_dict == 'dict'
                defaults = [self.traverse(n, indent='') for n in kw_dict[:-2]]
                names = eval(self.traverse(kw_dict[-2]))
                assert len(defaults) == len(names)
                sep = ''
                # FIXME: possibly handle line breaks
                for i, n in enumerate(names):
                    self.write(sep)
                    self.write("%s=%s" % (n, defaults[i]))
                    sep = ', '
                    ends_in_comma = False
                    pass
                pass
        pass

    if code_has_star_star_arg(code):
        if argc > 0 and not ends_in_comma:
            self.write(', ')
        self.write('**%s' % code.co_varnames[argc + kw_pairs])

    if is_lambda:
        self.write(": ")
    else:
        self.println("):")

    if len(code.co_consts) > 0 and code.co_consts[0] is not None and not is_lambda: # ugly
        # docstring exists, dump it
        print_docstring(self, self.indent, code.co_consts[0])

    scanner_code._tokens = None # save memory
    assert ast == 'stmts'

    all_globals = find_all_globals(ast, set())
    globals, nonlocals = find_globals_and_nonlocals(ast, set(),
                                                    set(), code, self.version)

    for g in sorted((all_globals & self.mod_globs) | globals):
        self.println(self.indent, 'global ', g)

    for nl in sorted(nonlocals):
        self.println(self.indent, 'nonlocal ', nl)

    self.mod_globs -= all_globals
    has_none = 'None' in code.co_names
    rn = has_none and not find_none(ast)
    self.gen_source(ast, code.co_name, scanner_code._customize, is_lambda=is_lambda,
                    returnNone=rn)
    scanner_code._tokens = None; scanner_code._customize = None # save memory
