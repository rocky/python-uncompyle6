'''
  Copyright (c) 1999 John Aycock
  Copyright (c) 2000-2002 by hartmut Goebel <h.goebel@crazy-compilers.com>
  Copyright (c) 2005 by Dan Pascu <dan@windowmaker.org>

  See main module for license.


  Decompilation (walking AST)

  All table-driven.  Step 1 determines a table (T) and a path to a
  table key (K) from the node type (N) (other nodes are shown as O):

         N                  N               N&K
     / | ... \          / | ... \        / | ... \
    O  O      O        O  O      K      O  O      O
              |
              K

  MAP_R0 (TABLE_R0)  MAP_R (TABLE_R)  MAP_DIRECT (TABLE_DIRECT)

  The default is a direct mapping.  The key K is then extracted from the
  subtree and used to find a table entry T[K], if any.  The result is a
  format string and arguments (a la printf()) for the formatting engine.
  Escapes in the format string are:

	%c	evaluate N[A] recursively*
	%C	evaluate N[A[0]]..N[A[1]-1] recursively, separate by A[2]*
	%,	print ',' if last %C only printed one item (for tuples--unused)
	%|	tab to current indentation level
	%+	increase current indentation level
	%-	decrease current indentation level
	%{...}	evaluate ... in context of N
	%%	literal '%'

  * indicates an argument (A) required.

  The '%' may optionally be followed by a number (C) in square brackets, which
  makes the engine walk down to N[C] before evaluating the escape code.
'''

import sys, re, cStringIO
from types import ListType, TupleType, DictType, \
     EllipsisType, IntType, CodeType

from spark import GenericASTTraversal
import parser
from parser import AST
from scanner import Token, Code

minint = -sys.maxint-1

# Some ASTs used for comparing code fragments (like 'return None' at
# the end of functions).

RETURN_LOCALS = AST('return_stmt',
			  [ AST('ret_expr', [AST('expr', [ Token('LOAD_LOCALS') ])]),
			    Token('RETURN_VALUE')])


NONE = AST('expr', [ Token('LOAD_CONST', pattr=None) ] )

RETURN_NONE = AST('stmt',
		  [ AST('return_stmt',
			[ NONE, Token('RETURN_VALUE')]) ])

PASS = AST('stmts',
          [ AST('sstmt',
              [ AST('stmt',
                  [ AST('passstmt', [])])])])

ASSIGN_DOC_STRING = lambda doc_string: \
	AST('stmt',
	    [ AST('assign',
		  [ AST('expr', [ Token('LOAD_CONST', pattr=doc_string) ]),
		    AST('designator', [ Token('STORE_NAME', pattr='__doc__')])
		    ])])

BUILD_TUPLE_0 = AST('expr',
                    [ AST('build_list',
                          [ Token('BUILD_TUPLE_0') ])])
		    
NAME_MODULE = AST('stmt',
                [ AST('assign',
                    [ AST('expr', [Token('LOAD_NAME', pattr='__name__')]),
                      AST('designator', [ Token('STORE_NAME', pattr='__module__')])
                      ])])

#TAB = '\t'			# as God intended
TAB = ' ' *4   # is less spacy than "\t"
INDENT_PER_LEVEL = ' ' # additional intent per pretty-print level

TABLE_R = {
    'POP_TOP':		( '%|%c\n', 0 ),
    'STORE_ATTR':	( '%c.%[1]{pattr}', 0),
#   'STORE_SUBSCR':	( '%c[%c]', 0, 1 ),
    'STORE_SLICE+0':	( '%c[:]', 0 ),
    'STORE_SLICE+1':	( '%c[%p:]', 0, (1,100) ),
    'STORE_SLICE+2':	( '%c[:%p]', 0, (1,100) ),
    'STORE_SLICE+3':	( '%c[%p:%p]', 0, (1,100), (2,100) ),
    'DELETE_SLICE+0':	( '%|del %c[:]\n', 0 ),
    'DELETE_SLICE+1':	( '%|del %c[%c:]\n', 0, 1 ),
    'DELETE_SLICE+2':	( '%|del %c[:%c]\n', 0, 1 ),
    'DELETE_SLICE+3':	( '%|del %c[%c:%c]\n', 0, 1, 2 ),
    'DELETE_ATTR':	( '%|del %c.%[-1]{pattr}\n', 0 ),
#   'EXEC_STMT':	( '%|exec %c in %[1]C\n', 0, (0,sys.maxint,', ') ),
}
TABLE_R0 = {
#    'BUILD_LIST':	( '[%C]',      (0,-1,', ') ),
#    'BUILD_TUPLE':	( '(%C)',      (0,-1,', ') ),
#    'CALL_FUNCTION':	( '%c(%C)', 0, (1,-1,', ') ),
}
TABLE_DIRECT = {
    'BINARY_ADD':	( '+' ,),
    'BINARY_SUBTRACT':	( '-' ,),
    'BINARY_MULTIPLY':	( '*' ,),
    'BINARY_DIVIDE':	( '/' ,),
    'BINARY_TRUE_DIVIDE':	( '/' ,),
    'BINARY_FLOOR_DIVIDE':	( '//' ,),
    'BINARY_MODULO':	( '%%',),
    'BINARY_POWER':	( '**',),
    'BINARY_LSHIFT':	( '<<',),
    'BINARY_RSHIFT':	( '>>',),
    'BINARY_AND':	( '&' ,),
    'BINARY_OR':	( '|' ,),
    'BINARY_XOR':	( '^' ,),
    'INPLACE_ADD':	( '+=' ,),
    'INPLACE_SUBTRACT':	( '-=' ,),
    'INPLACE_MULTIPLY':	( '*=' ,),
    'INPLACE_DIVIDE':	( '/=' ,),
    'INPLACE_TRUE_DIVIDE':	( '/=' ,),
    'INPLACE_FLOOR_DIVIDE':	( '//=' ,),
    'INPLACE_MODULO':	( '%%=',),
    'INPLACE_POWER':	( '**=',),
    'INPLACE_LSHIFT':	( '<<=',),
    'INPLACE_RSHIFT':	( '>>=',),
    'INPLACE_AND':	( '&=' ,),
    'INPLACE_OR':	( '|=' ,),
    'INPLACE_XOR':	( '^=' ,),
    'binary_expr':	( '%c %c %c', 0, -1, 1 ),
    
    'UNARY_POSITIVE':	( '+',),
    'UNARY_NEGATIVE':	( '-',),
    'UNARY_INVERT':	( '~%c'),
    'unary_expr':   ( '%c%c', 1, 0),
    
    'unary_not':	( 'not %c', 0 ),
    'unary_convert':	( '`%c`', 0 ),
    'get_iter':	( 'iter(%c)', 0 ),
    'slice0':		( '%c[:]', 0 ),
    'slice1':		( '%c[%p:]', 0, (1,100) ),
    'slice2':		( '%c[:%p]', 0, (1,100) ),
    'slice3':		( '%c[%p:%p]', 0, (1,100), (2,100) ),

    'IMPORT_FROM':	( '%{pattr}', ),
    'load_attr':	( '%c.%[1]{pattr}', 0),
    'LOAD_FAST':	( '%{pattr}', ),
    'LOAD_NAME':	( '%{pattr}', ),
    'LOAD_GLOBAL':	( '%{pattr}', ),
    'LOAD_DEREF':	( '%{pattr}', ),
    'LOAD_LOCALS':	( 'locals()', ),
    'LOAD_ASSERT':  ( '%{pattr}', ),
#   'LOAD_CONST':	( '%{pattr}', ),	# handled by n_LOAD_CONST
    'DELETE_FAST':	( '%|del %{pattr}\n', ),
    'DELETE_NAME':	( '%|del %{pattr}\n', ),
    'DELETE_GLOBAL':	( '%|del %{pattr}\n', ),
    'delete_subscr':	( '%|del %c[%c]\n', 0, 1,),
    'binary_subscr':	( '%c[%p]', 0, (1,100)),
    'binary_subscr2':	( '%c[%p]', 0, (1,100)),
    'store_subscr':	( '%c[%c]', 0, 1),
    'STORE_FAST':	( '%{pattr}', ),
    'STORE_NAME':	( '%{pattr}', ),
    'STORE_GLOBAL':	( '%{pattr}', ),
    'STORE_DEREF':	( '%{pattr}', ),
    'unpack':		( '%C%,', (1, sys.maxint, ', ') ),
    'unpack_w_parens':		( '(%C%,)', (1, sys.maxint, ', ') ),
    'unpack_list':	( '[%C]', (1, sys.maxint, ', ') ),
    'build_tuple2':	( '%P', (0,-1,', ', 100) ),

    #'list_compr':	( '[ %c ]', -2),	# handled by n_list_compr
    'list_iter':	( '%c', 0),
    'list_for':		( ' for %c in %c%c', 2, 0, 3 ),
    'list_if':		( ' if %c%c', 0, 2 ),
    'list_if_not':		( ' if not %p%c', (0,22), 2 ),
    'lc_body':		( '', ),	# ignore when recusing

    'comp_iter':	( '%c', 0),
    'comp_for':		( ' for %c in %c%c', 2, 0, 3 ),
    'comp_if':		( ' if %c%c', 0, 2 ),
    'comp_ifnot':	( ' if not %p%c', (0,22), 2 ),
    'comp_body':	( '', ),	# ignore when recusing
    'set_comp_body':    ( '%c', 0 ),
    'gen_comp_body':    ( '%c', 0 ),
    'dict_comp_body':   ( '%c:%c', 1, 0 ),
    
    'assign':		( '%|%c = %p\n', -1, (0,200) ),
    'augassign1':	( '%|%c %c %c\n', 0, 2, 1),
    'augassign2':	( '%|%c.%[2]{pattr} %c %c\n', 0, -3, -4),
#   'dup_topx':		( '%c', 0),
    'designList':	( '%c = %c', 0, -1 ),
    'and':          	( '%c and %c', 0, 2 ),
    'ret_and':        	( '%c and %c', 0, 2 ),
    'and2':          	( '%c', 3 ),
    'or':           	( '%c or %c', 0, 2 ),
    'ret_or':           	( '%c or %c', 0, 2 ),
    'conditional':  ( '%p if %p else %p', (2,27), (0,27), (4,27)),
    'ret_cond':     ( '%p if %p else %p', (2,27), (0,27), (4,27)),
    'conditionalnot':  ( '%p if not %p else %p', (2,27), (0,22), (4,27)),
    'ret_cond_not':  ( '%p if not %p else %p', (2,27), (0,22), (4,27)),
    'conditional_lambda':  ( '(%c if %c else %c)', 2, 0, 3),
    'return_lambda':    ('%c', 0),
    'compare':		( '%p %[-1]{pattr} %p', (0,19), (1,19) ),
    'cmp_list':		( '%p %p', (0,20), (1,19)),
    'cmp_list1':	( '%[3]{pattr} %p %p', (0,19), (-2,19)),
    'cmp_list2':	( '%[1]{pattr} %p', (0,19)),
#   'classdef': 	(), # handled by n_classdef()
    'funcdef':  	( '\n\n%|def %c\n', -2), # -2 to handle closures
    'funcdefdeco':  	( '\n\n%c', 0), 
    'mkfuncdeco':  	( '%|@%c\n%c', 0, 1), 
    'mkfuncdeco0':  	( '%|def %c\n', 0), 
    'classdefdeco':  	( '%c', 0), 
    'classdefdeco1':  	( '\n\n%|@%c%c', 0, 1), 
    'kwarg':    	( '%[0]{pattr}=%c', 1),
    'importlist2':	( '%C', (0, sys.maxint, ', ') ),
    
    'assert':		( '%|assert %c\n' , 0 ),
    'assert2':		( '%|assert %c, %c\n' , 0, 3 ),
    'assert_expr_or': ( '%c or %c', 0, 2 ),
    'assert_expr_and':    ( '%c and %c', 0, 2 ),
    'print_items_stmt': ( '%|print %c%c,\n', 0, 2),
    'print_items_nl_stmt': ( '%|print %c%c\n', 0, 2),
    'print_item':  ( ', %c', 0),
    'print_nl':	( '%|print\n', ),
    'print_to':		( '%|print >> %c, %c,\n', 0, 1 ),
    'print_to_nl':	( '%|print >> %c, %c\n', 0, 1 ),
    'print_nl_to':	( '%|print >> %c\n', 0 ),
    'print_to_items':	( '%C', (0, 2, ', ') ),

    'call_stmt':	( '%|%p\n', (0,200)),
    'break_stmt':	( '%|break\n', ),
    'continue_stmt':	( '%|continue\n', ),
    
    'raise_stmt0':	( '%|raise\n', ),
    'raise_stmt1':	( '%|raise %c\n', 0),
    'raise_stmt2':	( '%|raise %c, %c\n', 0, 1),
    'raise_stmt3':	( '%|raise %c, %c, %c\n', 0, 1, 2),
#    'yield':	( 'yield %c', 0),
#    'return_stmt':	( '%|return %c\n', 0),

    'ifstmt':		( '%|if %c:\n%+%c%-', 0, 1 ),
    'iflaststmt':		( '%|if %c:\n%+%c%-', 0, 1 ),
    'iflaststmtl':		( '%|if %c:\n%+%c%-', 0, 1 ),
    'testtrue':     ( 'not %p', (0,22) ),
    
    'ifelsestmt':	( '%|if %c:\n%+%c%-%|else:\n%+%c%-', 0, 1, 3 ),
    'ifelsestmtc':	( '%|if %c:\n%+%c%-%|else:\n%+%c%-', 0, 1, 3 ),
    'ifelsestmtl':	( '%|if %c:\n%+%c%-%|else:\n%+%c%-', 0, 1, 3 ),
    'ifelifstmt':	( '%|if %c:\n%+%c%-%c', 0, 1, 3 ),
    'elifelifstmt':	( '%|elif %c:\n%+%c%-%c', 0, 1, 3 ),
    'elifstmt':		( '%|elif %c:\n%+%c%-', 0, 1 ),
    'elifelsestmt':	( '%|elif %c:\n%+%c%-%|else:\n%+%c%-', 0, 1, 3 ),
    'ifelsestmtr':	( '%|if %c:\n%+%c%-%|else:\n%+%c%-', 0, 1, 2 ),
    'elifelsestmtr':	( '%|elif %c:\n%+%c%-%|else:\n%+%c%-\n\n', 0, 1, 2 ),

    'whilestmt':	( '%|while %c:\n%+%c%-\n\n', 1, 2 ),
    'while1stmt':	( '%|while 1:\n%+%c%-\n\n', 1 ),
    'while1elsestmt':  ( '%|while 1:\n%+%c%-%|else:\n%+%c%-\n\n', 1, 3 ),
    'whileelsestmt':	( '%|while %c:\n%+%c%-%|else:\n%+%c%-\n\n', 1, 2, -2 ),
    'whileelselaststmt':	( '%|while %c:\n%+%c%-%|else:\n%+%c%-', 1, 2, -2 ),
    'forstmt':		( '%|for %c in %c:\n%+%c%-\n\n', 3, 1, 4 ),
    'forelsestmt':	(
        '%|for %c in %c:\n%+%c%-%|else:\n%+%c%-\n\n', 3, 1, 4, -2),
    'forelselaststmt':	(
        '%|for %c in %c:\n%+%c%-%|else:\n%+%c%-', 3, 1, 4, -2),
    'forelselaststmtl':	(
        '%|for %c in %c:\n%+%c%-%|else:\n%+%c%-\n\n', 3, 1, 4, -2),
    'trystmt':		( '%|try:\n%+%c%-%c\n\n', 1, 3 ),
    'tryelsestmt':		( '%|try:\n%+%c%-%c%|else:\n%+%c%-\n\n', 1, 3, 4 ),
    'tryelsestmtc':		( '%|try:\n%+%c%-%c%|else:\n%+%c%-', 1, 3, 4 ),
    'tryelsestmtl':		( '%|try:\n%+%c%-%c%|else:\n%+%c%-', 1, 3, 4 ),
    'tf_trystmt':		( '%c%-%c%+', 1, 3 ),
    'tf_tryelsestmt':		( '%c%-%c%|else:\n%+%c', 1, 3, 4 ),
    'except':		( '%|except:\n%+%c%-', 3 ),
    'except_cond1':	( '%|except %c:\n', 1 ),
    'except_cond2':	( '%|except %c as %c:\n', 1, 5 ),
    'except_suite':     ( '%+%c%-%C', 0, (1, sys.maxint, '') ),
    'tryfinallystmt':	( '%|try:\n%+%c%-%|finally:\n%+%c%-\n\n', 1, 5 ),
    'withstmt':     ( '%|with %c:\n%+%c%-', 0, 3),
    'withasstmt':   ( '%|with %c as %c:\n%+%c%-', 0, 2, 3),
    'passstmt':		( '%|pass\n', ),
    'STORE_FAST':	( '%{pattr}', ),
    'kv':		( '%c: %c', 3, 1 ),
    'kv2':		( '%c: %c', 1, 2 ),
    'mapexpr':		( '{%[1]C}', (0,sys.maxint,', ') ),
    
    ##
    ## Python 2.5 Additions
    ##
    
    # Import style for 2.5
    'importstmt': ( '%|import %c\n', 2),
    'importstar': ( '%|from %[2]{pattr} import *\n', ),
    'importfrom': ( '%|from %[2]{pattr} import %c\n', 3 ),
    'importmultiple': ( '%|import %c%c\n', 2, 3),
    'import_cont'   : ( ', %c', 2),
    
    # CE - Fixes for tuples
    'assign2':     ( '%|%c, %c = %c, %c\n', 3, 4, 0, 1 ),
    'assign3':     ( '%|%c, %c, %c = %c, %c, %c\n', 5, 6, 7, 0, 1, 2 ),

}


MAP_DIRECT = (TABLE_DIRECT, )
MAP_R0 = (TABLE_R0, -1, 0)
MAP_R = (TABLE_R, -1)

MAP = {
    'stmt':		MAP_R,
    'call_function':		MAP_R,
    'del_stmt':		MAP_R,
    'designator':	MAP_R,
    'exprlist':		MAP_R0,
}

PRECEDENCE = {
    'build_list':           0,
    'mapexpr':              0,
    'unary_convert':        0,
    'dictcomp':             0,
    'setcomp':              0,
    'list_compr':           0,
    'genexpr':              0,
    
    'load_attr':            2,
    'binary_subscr':        2,
    'binary_subscr2':       2,
    'slice0':               2,
    'slice1':               2,
    'slice2':               2,
    'slice3':               2,
    'buildslice2':          2,
    'buildslice3':          2,
    'call_function':        2,
    
    'BINARY_POWER':         4,
    
    'unary_expr':           6,
    
    'BINARY_MULTIPLY':      8,
    'BINARY_DIVIDE':        8,
    'BINARY_TRUE_DIVIDE':   8,
    'BINARY_FLOOR_DIVIDE':  8,
    'BINARY_MODULO':        8,
    
    'BINARY_ADD':           10, 
    'BINARY_SUBTRACT':      10,
    
    'BINARY_LSHIFT':        12,
    'BINARY_RSHIFT':        12,
    
    'BINARY_AND':           14,
    
    'BINARY_XOR':           16,
    
    'BINARY_OR':            18,
    
    'cmp':                  20,
    
    'unary_not':            22,
    
    'and':                  24,
    'ret_and':              24,
    
    'or':                   26,
    'ret_or':               26,
    
    'conditional':          28,
    'conditionalnot':       28,
    'ret_cond':             28,
    'ret_cond_not':         28,
    
    '_mklambda':            30,
    'yield':                101
}

ASSIGN_TUPLE_PARAM = lambda param_name: \
             AST('expr', [ Token('LOAD_FAST', pattr=param_name) ])

escape = re.compile(r'''
            (?P<prefix> [^%]* )
            % ( \[ (?P<child> -? \d+ ) \] )?
                ((?P<type> [^{] ) |
                 ( [{] (?P<expr> [^}]* ) [}] ))
        ''', re.VERBOSE)

class ParserError(parser.ParserError):
    def __init__(self, error, tokens):
        self.error = error # previous exception
        self.tokens = tokens

    def __str__(self):
        lines = ['--- This code section failed: ---']
        lines.extend( map(str, self.tokens) )
        lines.extend( ['', str(self.error)] )
        return '\n'.join(lines)


def find_globals(node, globs):
    """Find globals in this statement."""
    for n in node:
        if isinstance(n, AST):
            globs = find_globals(n, globs)
        elif n.type in ('STORE_GLOBAL', 'DELETE_GLOBAL'):
            globs.add(n.pattr)
    return globs

def find_all_globals(node, globs):
    """Find globals in this statement."""
    for n in node:
        if isinstance(n, AST):
            globs = find_all_globals(n, globs)
        elif n.type in ('STORE_GLOBAL', 'DELETE_GLOBAL', 'LOAD_GLOBAL'):
            globs.add(n.pattr)
    return globs

def find_none(node):
    for n in node:
        if isinstance(n, AST):
            if not (n == 'return_stmt' or n == 'return_if_stmt'): 
                if find_none(n):
                    return True
        elif n.type == 'LOAD_CONST' and n.pattr == None:
            return True
    return False

class Walker(GenericASTTraversal, object):
    stacked_params = ('f', 'indent', 'isLambda', '_globals')

    def __init__(self, out, scanner, showast=0):
        GenericASTTraversal.__init__(self, ast=None)
        self.scanner = scanner
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

    def indentMore(self, indent=TAB):
        self.indent += indent
    def indentLess(self, indent=TAB):
        self.indent = self.indent[:-len(indent)]

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
    
    def write(self, *data):
        if (len(data) == 0) or (len(data) == 1 and data[0] == ''):
            return
#        import pdb; pdb.set_trace()
        out = ''.join((str(j) for j in data))
        n = 0
        for i in out:
            if i == '\n':
                n += 1
                if n == len(out):
                    self.pending_newlines = max(self.pending_newlines, n)
                    return
            elif n:
                self.pending_newlines = max(self.pending_newlines, n)
                out = out[n:]
                break
            else:
                break
                
        if self.pending_newlines > 0:
            self.f.write('\n'*self.pending_newlines)
            self.pending_newlines = 0
                
        for i in out[::-1]:
            if i == '\n':
                self.pending_newlines += 1
            else:
                break
        
        if self.pending_newlines:
            out = out[:-self.pending_newlines]
        self.f.write(out)

    def print_(self, *data):
        if data and not(len(data) == 1 and data[0] ==''):
            self.write(*data)
        self.pending_newlines = max(self.pending_newlines, 1)

    def print_docstring(self, indent, docstring):
        quote = '"""'
        self.write(indent)
        if type(docstring) == unicode:
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

        #Do a raw string if there are backslashes but no other escaped characters:
        #also check some edge cases
        if ('\t' in docstring
            and '\\' not in docstring
            and len(docstring) >= 2
            and docstring[-1] != '\t'
            and (docstring[-1] != '"'
                 or docstring[-2] == '\t')):
            self.write('r') #raw string
            #restore backslashes unescaped since raw
            docstring = docstring.replace('\t', '\\')
        else:
            #Escape '"' if it's the last character, so it doesn't ruin the ending triple quote
            if len(docstring) and docstring[-1] == '"':
                docstring = docstring[:-1] + '\\"'
            #Escape triple quote anywhere
            docstring = docstring.replace('"""', '\\"\\"\\"')
            #Restore escaped backslashes
            docstring = docstring.replace('\t', '\\\\')
        lines = docstring.split('\n')
        calculate_indent = sys.maxint
        for line in lines[1:]:
            stripped = line.lstrip()
            if len(stripped) > 0:
                calculate_indent = min(calculate_indent, len(line) - len(stripped))
        calculate_indent = min(calculate_indent, len(lines[-1]) - len(lines[-1].lstrip()))
        # Remove indentation (first line is special):
        trimmed = [lines[0]]
        if calculate_indent < sys.maxint:
            trimmed += [line[calculate_indent:] for line in lines[1:]]

        self.write(quote)
        if len(trimmed) == 0:
            self.print_(quote)
        elif len(trimmed) == 1:
            self.print_(trimmed[0], quote)
        else:
            self.print_(trimmed[0])
            for line in trimmed[1:-1]:
                self.print_( indent, line )
            self.print_(indent, trimmed[-1],quote)

            
    def n_return_stmt(self, node):
        if self.__params['isLambda']:
            self.preorder(node[0])
            self.prune()
        else:
            self.write(self.indent, 'return')
            if self.return_none or node != AST('return_stmt', [AST('ret_expr', [NONE]), Token('RETURN_VALUE')]):
                self.write(' ')
                self.preorder(node[0])
            self.print_()
            self.prune() # stop recursing
        
    def n_return_if_stmt(self, node):
        if self.__params['isLambda']:
            self.preorder(node[0])
            self.prune()
        else:
            self.write(self.indent, 'return')
            if self.return_none or node != AST('return_stmt', [AST('ret_expr', [NONE]), Token('RETURN_END_IF')]):
                self.write(' ')
                self.preorder(node[0])
            self.print_()
            self.prune() # stop recursing
        
    def n_yield(self, node):
        self.write('yield')
        if node != AST('yield', [NONE, Token('YIELD_VALUE')]):
            self.write(' ')
            self.preorder(node[0])
        self.prune() # stop recursing

    def n_buildslice3(self, node):
        p = self.prec
        self.prec = 100
        if node[0] != NONE:
            self.preorder(node[0])
        self.write(':')
        if node[1] != NONE:
            self.preorder(node[1])
        self.write(':')
        if node[2] != NONE:
            self.preorder(node[2])
        self.prec = p
        self.prune() # stop recursing

    def n_buildslice2(self, node):
        p = self.prec
        self.prec = 100
        if node[0] != NONE:
            self.preorder(node[0])
        self.write(':')
        if node[1] != NONE:
            self.preorder(node[1])
        self.prec = p
        self.prune() # stop recursing

#    def n_l_stmts(self, node):
#        if node[0] == '_stmts':
#            if len(node[0]) >= 2 and node[0][1] == 'stmt':
#                if node[0][-1][0] == 'continue_stmt':
#                    del node[0][-1]
#        self.default(node)

    def n_expr(self, node):
        p = self.prec
        if node[0].type.startswith('binary_expr'):
            n = node[0][-1][0]
        else:
            n = node[0]
        self.prec = PRECEDENCE.get(n,-2)
        if n == 'LOAD_CONST' and repr(n.pattr)[0] == '-':
            self.prec = 6
        if p < self.prec:
            self.write('(')
            self.preorder(node[0])
            self.write(')')
        else:
            self.preorder(node[0])
        self.prec = p
        self.prune()
    
    def n_ret_expr(self, node):
        if len(node) == 1 and node[0] == 'expr':
            self.n_expr(node[0])
        else:
            self.n_expr(node)
    
    n_ret_expr_or_cond = n_expr
    
    def n_binary_expr(self, node):
        self.preorder(node[0])
        self.write(' ')
        self.preorder(node[-1])
        self.write(' ')
        self.prec -= 1
        self.preorder(node[1])
        self.prec += 1
        self.prune()
        
    def n_LOAD_CONST(self, node):
        data = node.pattr; datatype = type(data)
        if datatype is IntType and data == minint:
            # convert to hex, since decimal representation
            # would result in 'LOAD_CONST; UNARY_NEGATIVE'
            # change:hG/2002-02-07: this was done for all negative integers
            # todo: check whether this is necessary in Python 2.1
            self.write( hex(data) )
        elif datatype is EllipsisType:
            self.write('...')
        elif data is None:
            # LOAD_CONST 'None' only occurs, when None is
            # implicit eg. in 'return' w/o params
            # pass
            self.write('None')
        else:
            self.write(repr(data))
        # LOAD_CONST is a terminal, so stop processing/recursing early
        self.prune()


    def n_delete_subscr(self, node):
        if node[-2][0] == 'build_list' and node[-2][0][-1].type.startswith('BUILD_TUPLE'):
            if node[-2][0][-1] != 'BUILD_TUPLE_0':
                node[-2][0].type = 'build_tuple2'
        self.default(node)        
#        maybe_tuple = node[-2][-1]
#        if maybe_tuple.type.startswith('BUILD_TUPLE'):
#            maybe_tuple.type = 'build_tuple2'
#        self.default(node)

    n_store_subscr = n_binary_subscr = n_delete_subscr
        
#    'tryfinallystmt':	( '%|try:\n%+%c%-%|finally:\n%+%c%-', 1, 5 ),
    def n_tryfinallystmt(self, node):
        if len(node[1][0]) == 1 and node[1][0][0] == 'stmt':
            if node[1][0][0][0] == 'trystmt':
                node[1][0][0][0].type = 'tf_trystmt'
            if node[1][0][0][0] == 'tryelsestmt':
                node[1][0][0][0].type = 'tf_tryelsestmt'
        self.default(node)
        
    def n_exec_stmt(self, node):
        """
        exec_stmt ::= expr exprlist DUP_TOP EXEC_STMT
        exec_stmt ::= expr exprlist EXEC_STMT
        """
        self.write(self.indent, 'exec ')
        self.preorder(node[0])
        if node[1][0] != NONE:
            sep = ' in '
            for subnode in node[1]:
                self.write(sep); sep = ", "
                self.preorder(subnode)
        self.print_()
        self.prune() # stop recursing
            
    def n_ifelsestmt(self, node, preprocess=0):
        n = node[3][0]
        if len(n) == 1 == len(n[0]) and n[0] == '_stmts':
            n = n[0][0][0]
        elif n[0].type in ('lastc_stmt', 'lastl_stmt'):
            n = n[0][0]
        else:
            if not preprocess:
                self.default(node)
            return
        
        if n.type in ('ifstmt', 'iflaststmt', 'iflaststmtl'):
            node.type = 'ifelifstmt'
            n.type = 'elifstmt'
        elif n.type in ('ifelsestmtr',):
            node.type = 'ifelifstmt'
            n.type = 'elifelsestmtr'
        elif n.type in ('ifelsestmt', 'ifelsestmtc', 'ifelsestmtl'):
            node.type = 'ifelifstmt'
            self.n_ifelsestmt(n, preprocess=1)
            if n == 'ifelifstmt':
                n.type = 'elifelifstmt'
            elif n.type in ('ifelsestmt', 'ifelsestmtc', 'ifelsestmtl'):
                n.type = 'elifelsestmt'
        if not preprocess:
            self.default(node)
            
    n_ifelsestmtc = n_ifelsestmtl = n_ifelsestmt
        
    def n_ifelsestmtr(self, node):
        if len(node[2]) != 2:
            self.default(node)

        if not (node[2][0][0][0] == 'ifstmt' and node[2][0][0][0][1][0] == 'return_if_stmts') \
                and not (node[2][0][-1][0] == 'ifstmt' and node[2][0][-1][0][1][0] == 'return_if_stmts'):
            self.default(node)
            return
        
        self.write(self.indent, 'if ')
        self.preorder(node[0])
        self.print_(':')
        self.indentMore()
        self.preorder(node[1])
        self.indentLess()
        
        if_ret_at_end = False
        if len(node[2][0]) >= 3:
            if node[2][0][-1][0] == 'ifstmt' and node[2][0][-1][0][1][0] == 'return_if_stmts':
                if_ret_at_end = True
                
        past_else = False
        prev_stmt_is_if_ret = True
        for n in node[2][0]:
            if (n[0] == 'ifstmt' and n[0][1][0] == 'return_if_stmts'):
                if prev_stmt_is_if_ret:
                    n[0].type = 'elifstmt'
                prev_stmt_is_if_ret = True
            else:
                prev_stmt_is_if_ret = False
                if not past_else and not if_ret_at_end:
                    self.print_(self.indent, 'else:')
                    self.indentMore()
                    past_else = True
            self.preorder(n)
        if not past_else or if_ret_at_end:
            self.print_(self.indent, 'else:')
            self.indentMore()
        self.preorder(node[2][1])
        self.indentLess()
        self.prune()
                       
    def n_elifelsestmtr(self, node):
        if len(node[2]) != 2:
            self.default(node)

        for n in node[2][0]:
            if not (n[0] == 'ifstmt' and n[0][1][0] == 'return_if_stmts'):
                self.default(node)
                return

        self.write(self.indent, 'elif ')
        self.preorder(node[0])
        self.print_(':')
        self.indentMore()
        self.preorder(node[1])
        self.indentLess()
        
        if_ret_at_end = False
        if len(node[2][0]) >= 3:
            if node[2][0][-1][0] == 'ifstmt' and node[2][0][-1][0][1][0] == 'return_if_stmts':
                if_ret_at_end = True
                
        past_else = False
        prev_stmt_is_if_ret = True
        for n in node[2][0]:
            n[0].type = 'elifstmt'
            self.preorder(n)
        self.print_(self.indent, 'else:')
        self.indentMore()
        self.preorder(node[2][1])
        self.indentLess()
        self.prune()

    def n_import_as(self, node):
        iname = node[0].pattr;
        assert node[-1][-1].type.startswith('STORE_')
        sname = node[-1][-1].pattr # assume one of STORE_.... here
        if iname == sname or iname.startswith(sname + '.'):
            self.write(iname)
        else:
            self.write(iname, ' as ', sname)
        self.prune() # stop recursing
    
    n_import_as_cont = n_import_as

    def n_importfrom(self, node):
        if node[0].pattr > 0:
            node[2].pattr = '.'*node[0].pattr+node[2].pattr
        self.default(node)
        
    n_importstar = n_importfrom
    
    def n_mkfunc(self, node):
        self.write(node[-2].attr.co_name) # = code.co_name
        self.indentMore()
        self.make_function(node, isLambda=0)
        if len(self.__param_stack) > 1:
            self.write('\n\n')
        else:
            self.write('\n\n\n')
        self.indentLess()
        self.prune() # stop recursing

    def n_mklambda(self, node):
        self.make_function(node, isLambda=1)
        self.prune() # stop recursing

    def n_list_compr(self, node):
        p = self.prec
        self.prec = 27
        n = node[-1]
        assert n == 'list_iter'
        # find innerst node
        while n == 'list_iter':
            n = n[0] # recurse one step
            if   n == 'list_for':	n = n[3]
            elif n == 'list_if':	n = n[2]
            elif n == 'list_if_not': n= n[2]
        assert n == 'lc_body'
        self.write( '[ '); 
        self.preorder(n[0]) # lc_body
        self.preorder(node[-1]) # for/if parts
        self.write( ' ]')
        self.prec = p
        self.prune() # stop recursing
    
    def comprehension_walk(self, node, iter_index):
        p = self.prec
        self.prec = 27
        code = node[-5].attr

        assert type(code) == CodeType
        code = Code(code, self.scanner, self.currentclass)
        #assert isinstance(code, Code)

        ast = self.build_ast(code._tokens, code._customize)
        self.customize(code._customize)
        ast = ast[0][0][0]
        
        n = ast[iter_index]
        assert n == 'comp_iter'
        # find innerst node
        while n == 'comp_iter':
            n = n[0] # recurse one step
            if   n == 'comp_for':	n = n[3]
            elif n == 'comp_if':	n = n[2]
            elif n == 'comp_ifnot': n = n[2]
        assert n == 'comp_body', ast

        self.preorder(n[0])
        self.write(' for ')
        self.preorder(ast[iter_index-1])
        self.write(' in ')
        self.preorder(node[-3])
        self.preorder(ast[iter_index])
        self.prec = p

    def n_genexpr(self, node):
        self.write('(')
        self.comprehension_walk(node, 3)
        self.write(')')
        self.prune()
        

    def n_setcomp(self, node):
        self.write('{')
        self.comprehension_walk(node, 4)
        self.write('}')
        self.prune()

    n_dictcomp = n_setcomp
       
    
    def n_classdef(self, node):
        # class definition ('class X(A,B,C):')
        cclass = self.currentclass
        self.currentclass = str(node[0].pattr)

        self.write('\n\n')
        self.write(self.indent, 'class ', self.currentclass)
        self.print_super_classes(node)
        self.print_(':')
        
        # class body
        self.indentMore()
        self.build_class(node[2][-2].attr)
        self.indentLess()
        
        self.currentclass = cclass
        if len(self.__param_stack) > 1:
            self.write('\n\n')
        else:
            self.write('\n\n\n')

        self.prune()


    n_classdefdeco2 = n_classdef

    def print_super_classes(self, node):
        node = node[1][0]
        if not (node == 'build_list'):
            return
            
        self.write('(')        
        line_separator = ', '
        sep = ''
        for elem in node[:-1]:
            value = self.traverse(elem)
            self.write(sep, value)
            sep = line_separator

        self.write(')')

    def n_mapexpr(self, node):
        """
        prettyprint a mapexpr
        'mapexpr' is something like k = {'a': 1, 'b': 42 }"
        """
        p = self.prec
        self.prec = 100
        assert node[-1] == 'kvlist'
        node = node[-1] # goto kvlist

        self.indentMore(INDENT_PER_LEVEL)
        line_seperator = ',\n' + self.indent
        sep = INDENT_PER_LEVEL[:-1]
        self.write('{')
        for kv in node:
            assert kv in ('kv', 'kv2', 'kv3')
            # kv ::= DUP_TOP expr ROT_TWO expr STORE_SUBSCR
            # kv2 ::= DUP_TOP expr expr ROT_THREE STORE_SUBSCR
            # kv3 ::= expr expr STORE_MAP
            if kv == 'kv':
                name = self.traverse(kv[-2], indent='');
                value = self.traverse(kv[1], indent=self.indent+(len(name)+2)*' ')
            elif kv == 'kv2':
                name = self.traverse(kv[1], indent='');
                value = self.traverse(kv[-3], indent=self.indent+(len(name)+2)*' ')
            elif kv == 'kv3':
                name = self.traverse(kv[-2], indent='');
                value = self.traverse(kv[0], indent=self.indent+(len(name)+2)*' ')
            self.write(sep, name, ': ', value)
            sep = line_seperator
        self.write('}')
        self.indentLess(INDENT_PER_LEVEL)
        self.prec = p
        self.prune()
        

    def n_build_list(self, node):
        """
        prettyprint a list or tuple
        """
        p = self.prec
        self.prec = 100
        lastnode = node.pop().type
        if lastnode.startswith('BUILD_LIST'):
            self.write('['); endchar = ']'
        elif lastnode.startswith('BUILD_TUPLE'):
            self.write('('); endchar = ')'
        elif lastnode.startswith('BUILD_SET'):
            self.write('{'); endchar = '}'
        elif lastnode.startswith('ROT_TWO'):
            self.write('('); endchar = ')'
        else:
            raise 'Internal Error: n_build_list expects list or tuple'
        
        self.indentMore(INDENT_PER_LEVEL)
        if len(node) > 3:
            line_separator = ',\n' + self.indent
        else:
            line_separator = ', '
        sep = INDENT_PER_LEVEL[:-1]
        for elem in node:
            if (elem == 'ROT_THREE'):
                continue

            assert elem == 'expr'
            value = self.traverse(elem)
            self.write(sep, value)
            sep = line_separator
        if len(node) == 1 and lastnode.startswith('BUILD_TUPLE'):
            self.write(',')
        self.write(endchar)
        self.indentLess(INDENT_PER_LEVEL)
        self.prec = p
        self.prune()

    def n_unpack(self, node):
        for n in node[1:]:
            if n[0].type == 'unpack':
                n[0].type = 'unpack_w_parens'
        self.default(node)
    
    n_unpack_w_parens = n_unpack
    
    def n_assign2(self, node):
        for n in node[-2:]:
            if n[0] == 'unpack':
                n[0].type = 'unpack_w_parens'
        self.default(node)
        
    def n_assign3(self, node):
        for n in node[-3:]:
            if n[0] == 'unpack':
                n[0].type = 'unpack_w_parens'
        self.default(node)

    def n_except_cond2(self, node):
        if node[5][0] == 'unpack':
            node[5][0].type = 'unpack_w_parens'
        self.default(node)
    
    def engine(self, entry, startnode):
        #self.print_("-----")
        #self.print_(str(startnode.__dict__))

        fmt = entry[0]
        ## no longer used, since BUILD_TUPLE_n is pretty printed:
        ##lastC = 0
        arg = 1
        i = 0

        m = escape.search(fmt)
        while m:
            i = m.end()
            self.write(m.group('prefix'))
                
            typ = m.group('type') or '{'
            node = startnode
            try:
                if m.group('child'):
                    node = node[int(m.group('child'))]
            except:
                print node.__dict__
                raise

            if   typ == '%':	self.write('%')
            elif typ == '+':	self.indentMore()
            elif typ == '-':	self.indentLess()
            elif typ == '|':	self.write(self.indent)
            ## no longer used, since BUILD_TUPLE_n is pretty printed:
            elif typ == ',':
                if lastC == 1:
                    self.write(',')
            elif typ == 'c':
                self.preorder(node[entry[arg]])
                arg += 1
            elif typ == 'p':
                p = self.prec
                (index, self.prec) = entry[arg]
                self.preorder(node[index])
                self.prec = p
                arg += 1
            elif typ == 'C':
                low, high, sep = entry[arg]
                lastC = remaining = len(node[low:high])
                ## remaining = len(node[low:high])
                for subnode in node[low:high]:
                    self.preorder(subnode)
                    remaining -= 1
                    if remaining > 0:
                        self.write(sep)
                arg += 1
            elif typ == 'P':
                p = self.prec
                low, high, sep, self.prec = entry[arg]
                lastC = remaining = len(node[low:high])
                ## remaining = len(node[low:high])
                for subnode in node[low:high]:
                    self.preorder(subnode)
                    remaining -= 1
                    if remaining > 0:
                        self.write(sep)
                self.prec = p
                arg += 1
            elif typ == '{':
                d = node.__dict__
                expr = m.group('expr')
                try:
                    self.write(eval(expr, d, d))
                except:
                    print node
                    raise
            m = escape.search(fmt, i)
        self.write(fmt[i:])
        
    def default(self, node):
           mapping = MAP.get(node, MAP_DIRECT)
           table = mapping[0]
           key = node

           for i in mapping[1:]:
              key = key[i]

           if table.has_key(key):
              self.engine(table[key], node)
              self.prune()

    def customize(self, customize):
       """
       Special handling for opcodes that take a variable number
       of arguments -- we add a new entry for each in TABLE_R.
       """
       for k, v in customize.items():
          if TABLE_R.has_key(k):
             continue
          op = k[ :k.rfind('_') ]
          if op == 'CALL_FUNCTION':	TABLE_R[k] = ('%c(%P)', 0, (1,-1,', ',100))
          elif op in ('CALL_FUNCTION_VAR',
                      'CALL_FUNCTION_VAR_KW', 'CALL_FUNCTION_KW'):
             if v == 0:
                str = '%c(%C' # '%C' is a dummy here ...
                p2 = (0, 0, None) # .. because of this
             else:
                str = '%c(%C, '
                p2 = (1,-2, ', ')
             if op == 'CALL_FUNCTION_VAR':
                str += '*%c)'
                entry = (str, 0, p2, -2)
             elif op == 'CALL_FUNCTION_KW':
                str += '**%c)'
                entry = (str, 0, p2, -2)
             else:
                str += '*%c, **%c)'
                if p2[2]: p2 = (1, -3, ', ')
                entry = (str, 0, p2, -3, -2)
             TABLE_R[k] = entry
          ## handled by n_mapexpr:
          ##if op == 'BUILD_SLICE':	TABLE_R[k] = ('%C'    ,    (0,-1,':'))
          ## handled by n_build_list:
          ##if   op == 'BUILD_LIST':	TABLE_R[k] = ('[%C]'  ,    (0,-1,', '))
          ##elif op == 'BUILD_TUPLE':	TABLE_R[k] = ('(%C%,)',    (0,-1,', '))

    def get_tuple_parameter(self, ast, name):
       """
       If the name of the formal parameter starts with dot,
       it's a tuple parameter, like this:
       #          def MyFunc(xx, (a,b,c), yy):
       #                  print a, b*2, c*42
       In byte-code, the whole tuple is assigned to parameter '.1' and
       then the tuple gets unpacked to 'a', 'b' and 'c'.

       Since identifiers starting with a dot are illegal in Python,
       we can search for the byte-code equivalent to '(a,b,c) = .1'
       """

       assert ast == 'stmts'
       for i in range(len(ast)):
           # search for an assign-statement
           assert ast[i][0] == 'stmt'
           node = ast[i][0][0]
           if node == 'assign' \
              and node[0] == ASSIGN_TUPLE_PARAM(name):
               # okay, this assigns '.n' to something
               del ast[i]
               # walk lhs; this
               # returns a tuple of identifiers as used
               # within the function definition
               assert node[1] == 'designator'
               # if lhs is not a UNPACK_TUPLE (or equiv.),
               # add parenteses to make this a tuple
               #if node[1][0] not in ('unpack', 'unpack_list'):
               return '(' + self.traverse(node[1]) + ')'
               #return self.traverse(node[1])
       raise Exception("Can't find tuple parameter " + name)


    def make_function(self, node, isLambda, nested=1):
        """Dump function defintion, doc string, and function body."""

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

            if default:
                if self.showast:
                    print '--', name
                    print default
                    print '--'
                result = '%s = %s' % (name, self.traverse(default, indent='') )
                if result[-2:] == '= ':	# default was 'LOAD_CONST None'
                    result += 'None'
                return result
            else:
                return name
        defparams = node[:node[-1].attr] # node[-1] == MAKE_xxx_n
        code = node[-2].attr

        assert type(code) == CodeType
        code = Code(code, self.scanner, self.currentclass)
        #assert isinstance(code, Code)

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
            self.write( str(p))
            self.ERROR = p
            return
            
        # build parameters
       
        ##This would be a nicer piece of code, but I can't get this to work
        ## now, have to find a usable lambda constuct  hG/2000-09-05
        ##params = map(lambda name, default: build_param(ast, name, default),
        ##	     paramnames, defparams)
        params = []
        for name, default in map(lambda a,b: (a,b), paramnames, defparams):
            params.append( build_param(ast, name, default) )

        params.reverse() # back to correct order

        if 4 & code.co_flags:	# flag 2 -> variable number of args
            params.append('*%s' % code.co_varnames[argc])
            argc += 1
        if 8 & code.co_flags:	# flag 3 -> keyword args
            params.append('**%s' % code.co_varnames[argc])
            argc += 1

        # dump parameter list (with default values)
        indent = self.indent
        if isLambda:
            self.write("lambda ", ", ".join(params), ": ")
        else:
            self.print_("(", ", ".join(params), "):")
            #self.print_(indent, '#flags:\t', int(code.co_flags))

        if len(code.co_consts)>0 and code.co_consts[0] != None and not isLambda: # ugly
            # docstring exists, dump it
            self.print_docstring(indent, code.co_consts[0])

        
        code._tokens = None # save memory
        assert ast == 'stmts'
        #if isLambda:
            # convert 'return' statement to expression
            #assert len(ast[0]) == 1  wrong, see 'lambda (r,b): r,b,g'
            #assert ast[-1] == 'stmt'
            #assert len(ast[-1]) == 1
#            assert ast[-1][0] == 'return_stmt'
#            ast[-1][0].type = 'return_lambda'
        #else:
        #    if ast[-1] == RETURN_NONE:
                # Python adds a 'return None' to the
                # end of any function; remove it
         #       ast.pop() # remove last node
        
        all_globals = find_all_globals(ast, set())
        for g in ((all_globals & self.mod_globs) | find_globals(ast, set())):
           self.print_(self.indent, 'global ', g)
        self.mod_globs -= all_globals
        rn = ('None' in code.co_names) and not find_none(ast)
        self.gen_source(ast, code._customize, isLambda=isLambda, returnNone=rn)
        code._tokens = None; code._customize = None # save memory
        
    def build_class(self, code):
        """Dump class definition, doc string and class body."""

        assert type(code) == CodeType
        code = Code(code, self.scanner, self.currentclass)
        #assert isinstance(code, Code)

        indent = self.indent
        #self.print_(indent, '#flags:\t', int(code.co_flags))
        ast = self.build_ast(code._tokens, code._customize)
        code._tokens = None # save memory
        assert ast == 'stmts'

        if ast[0][0] == NAME_MODULE:
            del ast[0]

        # if docstring exists, dump it
        if code.co_consts and code.co_consts[0] != None and ast[0][0] == ASSIGN_DOC_STRING(code.co_consts[0]):
            self.print_docstring(indent, code.co_consts[0])
            self.print_()
            del ast[0]
        

        # the function defining a class normally returns locals(); we
        # don't want this to show up in the source, thus remove the node
        if ast[-1][0] == RETURN_LOCALS:
            del ast[-1] # remove last node
        #else:
        #    print ast[-1][-1]

        for g in find_globals(ast, set()):
           self.print_(indent, 'global ', g)
           
        self.gen_source(ast, code._customize)
        code._tokens = None; code._customize = None # save memory


    def gen_source(self, ast, customize, isLambda=0, returnNone=False):
        """convert AST to source code"""

        rn = self.return_none
        self.return_none = returnNone
        # if code would be empty, append 'pass'
        if len(ast) == 0:
            self.print_(self.indent, 'pass')
        else:
            self.customize(customize)
            if isLambda:
                self.write(self.traverse(ast, isLambda=isLambda))
            else:
                self.print_(self.traverse(ast, isLambda=isLambda))            
        self.return_none = rn

    def build_ast(self, tokens, customize, isLambda=0, noneInNames=False):
        assert type(tokens) == ListType
        #assert isinstance(tokens[0], Token)

        if isLambda:
            tokens.append(Token('LAMBDA_MARKER'))
            try:
                ast = parser.parse(tokens, customize)
            except parser.ParserError, e:
                raise ParserError(e, tokens)
            if self.showast:
                self.print_(repr(ast))
            return ast        

        if len(tokens) >= 2 and not noneInNames:
            if tokens[-1] == Token('RETURN_VALUE'):
                if tokens[-2] == Token('LOAD_CONST'):
                    del tokens[-2:]
                else:
                    tokens.append(Token('RETURN_LAST'))
        if len(tokens) == 0:
            return PASS
        
        # Build AST from disassembly.
        try:
            ast = parser.parse(tokens, customize)
        except parser.ParserError, e:
            raise ParserError(e, tokens)

        if self.showast:
            self.print_(repr(ast))

        return ast
