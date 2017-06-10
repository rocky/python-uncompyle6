#  Copyright (c) 2015-2017 by Rocky Bernstein
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

# FIXME: put this in xdis
def code_has_star_arg(code):
    """Return True iff
    the code object has a variable positional parameter (*args-like)"""
    return (code.co_flags & 4) != 0

def code_has_star_star_arg(code):
    """Return True iff
    The code object has a variable keyword parameter (**kwargs-like)."""
    return (code.co_flags & 8) != 0

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
        while j >= l and node[j].type in ('annotate_arg' 'annotate_tuple'):
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

    if code_has_star_arg(code):
        self.write('*%s' % code.co_varnames[argc + kw_pairs])
        argc += 1

    i = len(paramnames) - len(defparams)
    suffix = ''
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
            self.write(suffix)
            param = paramnames[i]
            self.write(param)
            if param in annotate_args:
                aa = annotate_args[param]
                if isinstance(aa, tuple):
                    aa = aa[0]
                self.write(': "%s"' % aa)
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

    if isLambda:
        self.write(": ")
    else:
        self.write(')')
        if 'return' in annotate_tuple[0].attr:
            if (line_number != self.line_number):
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
        code.co_consts[0] is not None and not isLambda): # ugly
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
        annotate_argc  = 0
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

    if code_has_star_arg(code):
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

    if code_has_star_star_arg(code):
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

    # Thank you, Python, for a such a well-thought out system that has
    # changed 4 or so times.

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


    # Python 3.3+ adds a qualified name at TOS (-1)
    # moving down the LOAD_LAMBDA instruction
    if 3.0 <= self.version <= 3.2:
        lambda_index = -2
    elif 3.03 <= self.version:
        lambda_index = -3
    else:
        lambda_index = None

    args_node = node[-1]
    if isinstance(args_node.attr, tuple):
        pos_args, kw_args, annotate_argc  = args_node.attr
        if self.version <= 3.3 and len(node) > 2 and node[lambda_index] != 'LOAD_LAMBDA':
            # args are after kwargs; kwargs are bundled as one node
            defparams = node[1:args_node.attr[0]+1]
        else:
            # args are before kwargs; kwags as bundled as one node
            defparams = node[:args_node.attr[0]]
    else:
        if self.version < 3.6:
            defparams = node[:args_node.attr]
        else:
            default, kw, annotate, closure = args_node.attr
            # FIXME: start here for Python 3.6 and above:
            defparams = []
            # if default:
            #     defparams = node[-(2 +  kw + annotate  + closure)]
            # else:
            #     defparams = []

        kw_args  = 0
        pass


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
    if not 3.0 <= self.version <= 3.1:
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

    # build parameters
    params = [build_param(ast, name, d) for
              name, d in zip_longest(paramnames, defparams, fillvalue=None)]

    if not 3.0 <= self.version <= 3.1:
        params.reverse() # back to correct order

    if code_has_star_arg(code):
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
                elif self.version >= 3.4 and not (n.type in ('kwargs', 'kwarg')):
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

    if code_has_star_star_arg(code):
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
