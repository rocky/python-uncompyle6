import uncompyle2
from uncompyle2 import uncompyle, walker, verify, magics
from uncompyle2.spark import GenericASTTraversal, GenericASTTraversalPruningException
import sys, inspect, types, cStringIO

from collections import namedtuple
NodeInfo = namedtuple("NodeInfo", "node start finish")

class FindWalker(walker.Walker, object):
    stacked_params = ('f', 'indent', 'isLambda', '_globals')

    def __init__(self, out, scanner, showast=0):
        GenericASTTraversal.__init__(self, ast=None)
        params = {
            'f': out,
            'indent': '',
            }
        self.showast = showast
        self.__params = params
        self.__param_stack = []
        self.ERROR = None
        self.prec = 100
        self.return_none = False
        self.mod_globs = set()
        self.currentclass = None
        self.pending_newlines = 0

        self.found_offset = False
        self.offsets = {}


    f = property(lambda s: s.__params['f'],
                 lambda s, x: s.__params.__setitem__('f', x),
                 lambda s: s.__params.__delitem__('f'),
                 None)

    indent = property(lambda s: s.__params['indent'],
                 lambda s, x: s.__params.__setitem__('indent', x),
                 lambda s: s.__params.__delitem__('indent'),
                 None)

    isLambda = property(lambda s: s.__params['isLambda'],
                 lambda s, x: s.__params.__setitem__('isLambda', x),
                 lambda s: s.__params.__delitem__('isLambda'),
                 None)

    _globals = property(lambda s: s.__params['_globals'],
                 lambda s, x: s.__params.__setitem__('_globals', x),
                 lambda s: s.__params.__delitem__('_globals'),
                 None)

    def preorder(self, node=None):
        if node is None:
            node = self.ast

        if hasattr(node, 'offset'):
            start = len(self.f.getvalue())
            if node.offset == self.find_offset:
                self.found_offset = True
                # print 'BINGO!'

        try:
            name = 'n_' + self.typestring(node)
            if hasattr(self, name):
                func = getattr(self, name)
                func(node)
            else:
                self.default(node)
        except GenericASTTraversalPruningException:
            if hasattr(node, 'offset'):
                self.offsets[node.offset] = NodeInfo(node = node,
                                                     start = start,
                                                     finish = len(self.f.getvalue()))
                # print self.offsets[node.offset]
                # print self.f.getvalue()[start:]
            return

        for kid in node:
            self.preorder(kid)

        name = name + '_exit'
        if hasattr(self, name):
            func = getattr(self, name)
            func(node)

        return


    def find_source(self, offset, ast, customize, isLambda=0, returnNone=False):
        """convert AST to source code"""

        self.find_offset = offset
        self.found_offset = False

        # FIXME; the below doesn't find self.__params
        # work so we duplicate the code.
        # self.gen_source(ast, customize, isLambda, returnNone)
        rn = self.return_none
        self.return_none = returnNone
        # if code would be empty, append 'pass'
        if len(ast) == 0:
            self.print_(self.indent, 'pass')
        else:
            self.customize(customize)
            result = self.traverse(ast, isLambda=isLambda)
            if isLambda:
                self.write(result)
            else:
                self.print_(result)
        self.return_none = rn

    # FIXME; below duplicated the code, since we don't find self.__params
    def traverse(self, node, indent=None, isLambda=0):

        self.__param_stack.append(self.__params)
        if indent is None: indent = self.indent
        p = self.pending_newlines
        self.pending_newlines = 0
        self.__params = {
            '_globals': {},
            'f': cStringIO.StringIO(),
            'indent': indent,
            'isLambda': isLambda,
            }
        self.preorder(node)
        self.f.write('\n'*self.pending_newlines)

        result = self.f.getvalue()

        self.__params = self.__param_stack.pop()
        self.pending_newlines = p
        return result
    pass

def uncompyle_find(version, co, find_offset, out=sys.stdout, showasm=0, showast=0):
    assert type(co) == types.CodeType
    # store final output stream for case of error
    __real_out = out or sys.stdout
    if version == 2.7:
        import uncompyle2.scanner27 as scan
        scanner = scan.Scanner27()
    elif version == 2.6:
        import scanner26 as scan
        scanner = scan.Scanner26()
    elif version == 2.5:
        import scanner25 as scan
        scanner = scan.Scanner25()
    scanner.setShowAsm(0, out)
    tokens, customize = scanner.disassemble(co)

    #  Build AST from disassembly.
    # walk = walker.Walker(out, scanner, showast=showast)
    walk = FindWalker(out, scanner, showast=showast)

    try:
        ast = walk.build_ast(tokens, customize)
    except walker.ParserError, e :  # parser failed, dump disassembly
        print >>__real_out, e
        raise
    del tokens # save memory

    # convert leading '__doc__ = "..." into doc string
    assert ast == 'stmts'
    try:
        if ast[0][0] == walker.ASSIGN_DOC_STRING(co.co_consts[0]):
            if find_offset == 0:
                walk.print_docstring('', co.co_consts[0])
                return
            del ast[0]
        if ast[-1] == walker.RETURN_NONE:
            ast.pop() # remove last node
            #todo: if empty, add 'pass'
    except:
        pass
    walk.mod_globs = walker.find_globals(ast, set())
    # walk.gen_source(ast, customize)
    walk.find_source(find_offset, ast, customize)
    for g in walk.mod_globs:
        walk.write('global %s ## Warning: Unused global' % g)
    if walk.ERROR:
        raise walk.ERROR

    return

def uncompyle_test():
    frame = inspect.currentframe()
    try:
        co = frame.f_code
        uncompyle(2.7, co, sys.stdout, 1)
        print
        print '------------------------'
        uncompyle_find(2.7, co, 33)
    finally:
        del frame

uncompyle_test()
