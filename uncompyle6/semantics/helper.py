import sys

from uncompyle6.parsers.treenode import SyntaxTree

from uncompyle6 import PYTHON3
if PYTHON3:
    minint = -sys.maxsize-1
    maxint = sys.maxsize
else:
    minint = -sys.maxint-1
    maxint = sys.maxint

read_write_global_ops = frozenset(('STORE_GLOBAL', 'DELETE_GLOBAL', 'LOAD_GLOBAL'))
read_global_ops       = frozenset(('STORE_GLOBAL', 'DELETE_GLOBAL'))

# NOTE: we also need to check that the variable name is a free variable, not a cell variable.
nonglobal_ops         = frozenset(('STORE_DEREF',  'DELETE_DEREF'))

# FIXME: this and find_globals could be paramaterized with one of the
# above global ops
def find_all_globals(node, globs):
    """Search Syntax Tree node to find variable names that are global."""
    for n in node:
        if isinstance(n, SyntaxTree):
            globs = find_all_globals(n, globs)
        elif n.kind in read_write_global_ops:
            globs.add(n.pattr)
    return globs

def find_globals_and_nonlocals(node, globs, nonlocals, code, version):
    """search a node of parse tree to find variable names that need a
    either 'global' or 'nonlocal' statements added."""
    for n in node:
        if isinstance(n, SyntaxTree):
            globs, nonlocals = find_globals_and_nonlocals(n, globs, nonlocals,
                                                          code, version)
        elif n.kind in read_global_ops:
            globs.add(n.pattr)
        elif (version >= 3.0
              and n.kind in nonglobal_ops
              and n.pattr in code.co_freevars
              and n.pattr != code.co_name
              and code.co_name != '<lambda>'):
            nonlocals.add(n.pattr)
    return globs, nonlocals

# def find_globals(node, globs, global_ops=mkfunc_globals):
#     """Find globals in this statement."""
#     for n in node:
#         # print("XXX", n.kind, global_ops)
#         if isinstance(n, SyntaxTree):
#             # FIXME: do I need a caser for n.kind="mkfunc"?
#             if n.kind in ("conditional_lambda", "return_lambda"):
#                 globs = find_globals(n, globs, mklambda_globals)
#             else:
#                 globs = find_globals(n, globs, global_ops)
#         elif n.kind in frozenset(global_ops):
#             globs.add(n.pattr)
#     return globs

def find_none(node):
    for n in node:
        if isinstance(n, SyntaxTree):
            if n not in ('return_stmt', 'return_if_stmt'):
                if find_none(n):
                    return True
        elif n.kind == 'LOAD_CONST' and n.pattr is None:
            return True
    return False

def print_docstring(self, indent, docstring):
    try:
        if docstring.find('"""') == -1:
            quote = '"""'
        else:
            quote = "'''"
            docstring = docstring.replace("'''", "\\'''")
    except:
        return False
    self.write(indent)
    if not PYTHON3 and not isinstance(docstring, str):
        # Must be unicode in Python2
        self.write('u')
        docstring = repr(docstring.expandtabs())[2:-1]
    else:
        docstring = repr(docstring.expandtabs())[1:-1]

    for (orig, replace) in (('\\\\', '\t'),
                            ('\\r\\n', '\n'),
                            ('\\n', '\n'),
                            ('\\r', '\n'),
                            ('\\"', '"'),
                            ("\\'", "'")):
        docstring = docstring.replace(orig, replace)

    # Do a raw string if there are backslashes but no other escaped characters:
    # also check some edge cases
    if ('\t' in docstring
        and '\\' not in docstring
        and len(docstring) >= 2
        and docstring[-1] != '\t'
        and (docstring[-1] != '"'
             or docstring[-2] == '\t')):
        self.write('r') # raw string
        # restore backslashes unescaped since raw
        docstring = docstring.replace('\t', '\\')
    else:
        # Escape '"' if it's the last character, so it doesn't
        # ruin the ending triple quote
        if len(docstring) and docstring[-1] == '"':
            docstring = docstring[:-1] + '\\"'
        # Restore escaped backslashes
        docstring = docstring.replace('\t', '\\\\')
    # Escape triple quote when needed
    if quote == '""""':
        docstring = docstring.replace('"""', '\\"\\"\\"')
    lines = docstring.split('\n')
    calculate_indent = maxint
    for line in lines[1:]:
        stripped = line.lstrip()
        if len(stripped) > 0:
            calculate_indent = min(calculate_indent, len(line) - len(stripped))
    calculate_indent = min(calculate_indent, len(lines[-1]) - len(lines[-1].lstrip()))
    # Remove indentation (first line is special):
    trimmed = [lines[0]]
    if calculate_indent < maxint:
        trimmed += [line[calculate_indent:] for line in lines[1:]]

    self.write(quote)
    if len(trimmed) == 0:
        self.println(quote)
    elif len(trimmed) == 1:
        self.println(trimmed[0], quote)
    else:
        self.println(trimmed[0])
        for line in trimmed[1:-1]:
            self.println( indent, line )
        self.println(indent, trimmed[-1], quote)
    return True


def flatten_list(node):
    """
    List of expressions may be nested in groups of 32 and 1024
    items. flatten that out and return the list
    """
    flat_elems = []
    for elem in node:
        if elem == 'expr1024':
            for subelem in elem:
                assert subelem == 'expr32'
                for subsubelem in subelem:
                    flat_elems.append(subsubelem)
        elif elem == 'expr32':
            for subelem in elem:
                assert subelem == 'expr'
                flat_elems.append(subelem)
        else:
            flat_elems.append(elem)
            pass
        pass
    return flat_elems


# if __name__ == '__main__':
#     if PYTHON3:
#         from io import StringIO
#     else:
#         from StringIO import StringIO
#     class PrintFake():
#         def __init__(self):
#             self.pending_newlines = 0
#             self.f = StringIO()

#         def write(self, *data):
#             if (len(data) == 0) or (len(data) == 1 and data[0] == ''):
#                 return
#             out = ''.join((str(j) for j in data))
#             n = 0
#             for i in out:
#                 if i == '\n':
#                     n += 1
#                     if n == len(out):
#                         self.pending_newlines = max(self.pending_newlines, n)
#                         return
#                 elif n:
#                     self.pending_newlines = max(self.pending_newlines, n)
#                     out = out[n:]
#                     break
#                 else:
#                     break

#             if self.pending_newlines > 0:
#                 self.f.write('\n'*self.pending_newlines)
#                 self.pending_newlines = 0

#             for i in out[::-1]:
#                 if i == '\n':
#                     self.pending_newlines += 1
#                 else:
#                     break

#             if self.pending_newlines:
#                 out = out[:-self.pending_newlines]
#             self.f.write(out)
#         def println(self, *data):
#             if data and not(len(data) == 1 and data[0] ==''):
#                 self.write(*data)
#             self.pending_newlines = max(self.pending_newlines, 1)
#             return
#         pass

#     for doc in (
#             "Now is the time",
#             r'''func placeholder - with ("""\nstring\n""")''',
#             r'''func placeholder - ' and with ("""\nstring\n""")''',
#             r"""func placeholder - ' and with ('''\nstring\n''') and \"\"\"\nstring\n\"\"\" """
#             ):
#         o = PrintFake()
#         print_docstring(o, '  ', doc)
#         print(o.f.getvalue())
