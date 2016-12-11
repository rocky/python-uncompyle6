#  Copyright (c) 2015, 2016 by Rocky Bernstein
#  Copyright (c) 2000-2002 by hartmut Goebel <h.goebel@crazy-compilers.com>
"""
All the crazy things we have to do to handle Python functions
"""
from xdis.code import iscode
from uncompyle6.scanner import Code
from uncompyle6.parsers.astnode import AST
from uncompyle6 import PYTHON3
from uncompyle6.semantics.parser_error import ParserError
from uncompyle6.semantics.helper import print_docstring

if PYTHON3:
    from itertools import zip_longest
else:
    from itertools import izip_longest as zip_longest

from uncompyle6.show import maybe_show_ast_param_default

def find_all_globals(node, globs):
    """Find globals in this statement."""
    for n in node:
        if isinstance(n, AST):
            globs = find_all_globals(n, globs)
        elif n.type in ('STORE_GLOBAL', 'DELETE_GLOBAL', 'LOAD_GLOBAL'):
            globs.add(n.pattr)
    return globs

def find_globals(node, globs):
    """Find globals in this statement."""
    for n in node:
        if isinstance(n, AST):
            globs = find_globals(n, globs)
        elif n.type in ('STORE_GLOBAL', 'DELETE_GLOBAL'):
            globs.add(n.pattr)
    return globs

def find_none(node):
    for n in node:
        if isinstance(n, AST):
            if n not in ('return_stmt', 'return_if_stmt'):
                if find_none(n):
                    return True
        elif n.type == 'LOAD_CONST' and n.pattr is None:
            return True
    return False

# FIXME: DRY the below code...

def make_function3_annotate(self, node, isLambda, nested=1,
                            codeNode=None, annotate_last=-1):
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
            maybe_show_ast_param_default(self.showast, name, value)
            result = '%s=%s' % (name,  value)
            if result[-2:] == '= ':	# default was 'LOAD_CONST None'
                result += 'None'
            return result
        else:
            return name

    # MAKE_FUNCTION_... or MAKE_CLOSURE_...
    assert node[-1].type.startswith('MAKE_')

    annotate_tuple = node[annotate_last]
    annotate_args = {}

    if (annotate_tuple == 'annotate_tuple'
        and annotate_tuple[0] in ('LOAD_CONST', 'LOAD_NAME')
        and isinstance(annotate_tuple[0].attr, tuple)):
        annotate_tup = annotate_tuple[0].attr
        i = -1
        j = annotate_last-1
        l = -len(node)
        while j >= l and node[j].type in ('annotate_arg' 'annotate_tuple'):
            annotate_args[annotate_tup[i]] = (node[j][0].attr,
                                              node[j][0] == 'LOAD_CONST')
            i -= 1
            j -= 1

    args_node = node[-1]
    if isinstance(args_node.attr, tuple):
        # positional args are before kwargs
        defparams = node[:args_node.attr[0]]
        pos_args, kw_args, annotate_argc  = args_node.attr
    else:
        defparams = node[:args_node.attr]
        kw_args  = 0
        pass

    if 3.0 <= self.version <= 3.2:
        lambda_index = -2
    elif 3.03 <= self.version:
        lambda_index = -3
    else:
        lambda_index = None

    if lambda_index and isLambda and iscode(node[lambda_index].attr):
        assert node[lambda_index].type == 'LOAD_LAMBDA'
        code = node[lambda_index].attr
    else:
        code = codeNode.attr

    assert iscode(code)
    code = Code(code, self.scanner, self.currentclass)

    # add defaults values to parameter names
    argc = code.co_argcount
    paramnames = list(code.co_varnames[:argc])

    try:
        ast = self.build_ast(code._tokens,
                             code._customize,
                             isLambda = isLambda,
                             noneInNames = ('None' in code.co_names))
    except ParserError as p:
        self.write(str(p))
        self.ERROR = p
        return

    kw_pairs = args_node.attr[1]
    indent = self.indent

    if isLambda:
        self.write("lambda ")
    else:
        self.write("(")

    last_line = self.f.getvalue().split("\n")[-1]
    l = len(last_line)
    indent = ' ' * l
    line_number = self.line_number

    if 4 & code.co_flags:	# flag 2 -> variable number of args
        self.write('*%s' % code.co_varnames[argc + kw_pairs])
        argc += 1

    i = len(paramnames) - len(defparams)
    suffix = ''
    for param in paramnames[:i]:
        self.write(suffix, param)
        if param in annotate_args:
            value, string = annotate_args[param]
            if string:
                self.write(': "%s"' % value)
            else:
                self.write(': %s' % value)
        suffix = ', '

    suffix = ', ' if i > 0 else ''
    for n in node:
        if n == 'pos_arg':
            self.write(suffix)
            param = paramnames[i]
            self.write(param)
            if param in annotate_args:
                self.write(':"%s' % annotate_args[param])
            self.write('=')
            i += 1
            self.preorder(n)
            if (line_number != self.line_number):
                suffix = ",\n" + indent
                line_number = self.line_number
            else:
                suffix = ', '

    # self.println(indent, '#flags:\t', int(code.co_flags))
    if kw_args > 0:
        if not (4 & code.co_flags):
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
                self.write('%s=' % n[0].pattr)
                self.preorder(n[1])
                if i < last:
                    self.write(', ')
                i += 1
                pass
            pass
        pass

    if 8 & code.co_flags:	# flag 3 -> keyword args
        if argc > 0:
            self.write(', ')
        self.write('**%s' % code.co_varnames[argc + kw_pairs])

    if isLambda:
        self.write(": ")
    else:
        self.write(')')
        if 'return' in annotate_args:
            value, string = annotate_args['return']
            if string:
                self.write(' -> "%s"' % value)
            else:
                self.write(' -> %s' % value)

        self.println(":")

    if (len(code.co_consts) > 0 and
        code.co_consts[0] is not None and not isLambda): # ugly
        # docstring exists, dump it
        print_docstring(self, indent, code.co_consts[0])

    code._tokens = None # save memory
    assert ast == 'stmts'

    all_globals = find_all_globals(ast, set())
    for g in ((all_globals & self.mod_globs) | find_globals(ast, set())):
        self.println(self.indent, 'global ', g)
    self.mod_globs -= all_globals
    has_none = 'None' in code.co_names
    rn = has_none and not find_none(ast)
    self.gen_source(ast, code.co_name, code._customize, isLambda=isLambda,
                    returnNone=rn)
    code._tokens = code._customize = None # save memory

def make_function2(self, node, isLambda, nested=1, codeNode=None):
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
            maybe_show_ast_param_default(self.showast, name, value)
            result = '%s=%s' % (name,  value)
            if result[-2:] == '= ':	# default was 'LOAD_CONST None'
                result += 'None'
            return result
        else:
            return name

    # MAKE_FUNCTION_... or MAKE_CLOSURE_...
    assert node[-1].type.startswith('MAKE_')

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

    if lambda_index and isLambda and iscode(node[lambda_index].attr):
        assert node[lambda_index].type == 'LOAD_LAMBDA'
        code = node[lambda_index].attr
    else:
        code = codeNode.attr

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
                             isLambda = isLambda,
                             noneInNames = ('None' in code.co_names))
    except ParserError as p:
        self.write(str(p))
        self.ERROR = p
        return

    kw_pairs = args_node.attr[1] if self.version >= 3.0 else 0
    indent = self.indent

    # build parameters
    params = [build_param(ast, name, default) for
              name, default in zip_longest(paramnames, defparams, fillvalue=None)]
    params.reverse() # back to correct order

    if 4 & code.co_flags:	# flag 2 -> variable number of args
        params.append('*%s' % code.co_varnames[argc])
        argc += 1

    # dump parameter list (with default values)
    if isLambda:
        self.write("lambda ", ", ".join(params))
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

    if 8 & code.co_flags:	# flag 3 -> keyword args
        if argc > 0:
            self.write(', ')
        self.write('**%s' % code.co_varnames[argc + kw_pairs])

    if isLambda:
        self.write(": ")
    else:
        self.println("):")

    if len(code.co_consts) > 0 and code.co_consts[0] is not None and not isLambda: # ugly
        # docstring exists, dump it
        print_docstring(self, indent, code.co_consts[0])

    code._tokens = None # save memory
    assert ast == 'stmts'

    all_globals = find_all_globals(ast, set())
    for g in ((all_globals & self.mod_globs) | find_globals(ast, set())):
        self.println(self.indent, 'global ', g)
    self.mod_globs -= all_globals
    has_none = 'None' in code.co_names
    rn = has_none and not find_none(ast)
    self.gen_source(ast, code.co_name, code._customize, isLambda=isLambda,
                    returnNone=rn)
    code._tokens = None; code._customize = None # save memory


def make_function3(self, node, isLambda, nested=1, codeNode=None):
    """Dump function definition, doc string, and function body."""

    # FIXME: call make_function3 if we are self.version >= 3.0
    # and then simplify the below.

    def build_param(ast, name, default):
        """build parameters:
            - handle defaults
            - handle format tuple parameters
        """
        if default:
            value = self.traverse(default, indent='')
            maybe_show_ast_param_default(self.showast, name, value)
            result = '%s=%s' % (name,  value)
            if result[-2:] == '= ':	# default was 'LOAD_CONST None'
                result += 'None'
            return result
        else:
            return name

    # MAKE_FUNCTION_... or MAKE_CLOSURE_...
    assert node[-1].type.startswith('MAKE_')

    args_node = node[-1]
    if isinstance(args_node.attr, tuple):
        if self.version <= 3.3 and len(node) > 2 and node[-3] != 'LOAD_LAMBDA':
            # positional args are after kwargs
            defparams = node[1:args_node.attr[0]+1]
        else:
            # positional args are before kwargs
            defparams = node[:args_node.attr[0]]
        pos_args, kw_args, annotate_argc  = args_node.attr
    else:
        defparams = node[:args_node.attr]
        kw_args  = 0
        pass

    if 3.0 <= self.version <= 3.2:
        lambda_index = -2
    elif 3.03 <= self.version:
        lambda_index = -3
    else:
        lambda_index = None

    if lambda_index and isLambda and iscode(node[lambda_index].attr):
        assert node[lambda_index].type == 'LOAD_LAMBDA'
        code = node[lambda_index].attr
    else:
        code = codeNode.attr

    assert iscode(code)
    code = Code(code, self.scanner, self.currentclass)

    # add defaults values to parameter names
    argc = code.co_argcount
    paramnames = list(code.co_varnames[:argc])

    # defaults are for last n parameters, thus reverse
    if not 3.0 <= self.version <= 3.2:
        paramnames.reverse(); defparams.reverse()

    try:
        ast = self.build_ast(code._tokens,
                             code._customize,
                             isLambda = isLambda,
                             noneInNames = ('None' in code.co_names))
    except ParserError as p:
        self.write(str(p))
        self.ERROR = p
        return

    kw_pairs = args_node.attr[1] if self.version >= 3.0 else 0
    indent = self.indent

    # build parameters
    if self.version != 3.2:
        params = [build_param(ast, name, default) for
                  name, default in zip_longest(paramnames, defparams, fillvalue=None)]
        params.reverse() # back to correct order

        if 4 & code.co_flags:	# flag 2 -> variable number of args
            if self.version > 3.0:
                params.append('*%s' % code.co_varnames[argc + kw_pairs])
            else:
                params.append('*%s' % code.co_varnames[argc])
            argc += 1

        # dump parameter list (with default values)
        if isLambda:
            self.write("lambda ", ", ".join(params))
        else:
            self.write("(", ", ".join(params))
        # self.println(indent, '#flags:\t', int(code.co_flags))

    else:
        if isLambda:
            self.write("lambda ")
        else:
            self.write("(")
            pass

        last_line = self.f.getvalue().split("\n")[-1]
        l = len(last_line)
        indent = ' ' * l
        line_number = self.line_number

        if 4 & code.co_flags:	# flag 2 -> variable number of args
            self.write('*%s' % code.co_varnames[argc + kw_pairs])
            argc += 1

        i = len(paramnames) - len(defparams)
        self.write(", ".join(paramnames[:i]))
        suffix = ', ' if i > 0 else ''
        for n in node:
            if n == 'pos_arg':
                self.write(suffix)
                self.write(paramnames[i] + '=')
                i += 1
                self.preorder(n)
                if (line_number != self.line_number):
                    suffix = ",\n" + indent
                    line_number = self.line_number
                else:
                    suffix = ', '

    if kw_args > 0:
        if not (4 & code.co_flags):
            if argc > 0:
                self.write(", *, ")
            else:
                self.write("*, ")
            pass
        else:
            self.write(", ")

        if not 3.0 <= self.version <= 3.2:
            for n in node:
                if n == 'pos_arg':
                    continue
                elif self.version >= 3.4 and n.type != 'kwargs':
                    continue
                else:
                    self.preorder(n)
                break
        else:
            kwargs = node[0]
            last = len(kwargs)-1
            i = 0
            for n in node[0]:
                if n == 'kwarg':
                    self.write('%s=' % n[0].pattr)
                    self.preorder(n[1])
                    if i < last:
                        self.write(', ')
                    i += 1
                    pass
                pass
            pass
        pass

    if 8 & code.co_flags:	# flag 3 -> keyword args
        if argc > 0:
            self.write(', ')
        self.write('**%s' % code.co_varnames[argc + kw_pairs])

    if isLambda:
        self.write(": ")
    else:
        self.println("):")

    if len(code.co_consts) > 0 and code.co_consts[0] is not None and not isLambda: # ugly
        # docstring exists, dump it
        print_docstring(self, self.indent, code.co_consts[0])

    code._tokens = None # save memory
    assert ast == 'stmts'

    all_globals = find_all_globals(ast, set())
    for g in ((all_globals & self.mod_globs) | find_globals(ast, set())):
        self.println(self.indent, 'global ', g)
    self.mod_globs -= all_globals
    has_none = 'None' in code.co_names
    rn = has_none and not find_none(ast)
    self.gen_source(ast, code.co_name, code._customize, isLambda=isLambda,
                    returnNone=rn)
    code._tokens = None; code._customize = None # save memory
