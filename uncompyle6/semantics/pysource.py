#  Copyright (c) 2015, 2016 by Rocky Bernstein
#  Copyright (c) 2005 by Dan Pascu <dan@windowmaker.org>
#  Copyright (c) 2000-2002 by hartmut Goebel <h.goebel@crazy-compilers.com>
#  Copyright (c) 1999 John Aycock

"""Creates Python source code from an uncompyle6 abstract syntax tree.

The terminal symbols are CPython bytecode instructions. (See the
python documentation under module "dis" for a list of instructions
and what they mean).

Upper levels of the grammar is a more-or-less conventional grammar for
Python.

Semantic action rules for nonterminal symbols can be specified here by
creating a method prefaced with "n_" for that nonterminal. For
example, "n_exec_stmt" handles the semantic actions for the
"exec_smnt" nonterminal symbol. Similarly if a method with the name
of the nontermail is suffixed with "_exit" it will be called after
all of its children are called.

Another other way to specify a semantic rule for a nonterminal is via
rule given in one of the tables MAP_R0, MAP_R, or MAP_DIRECT.

These uses a printf-like syntax to direct substitution from attributes
of the nonterminal and its children..

The rest of the below describes how table-driven semantic actions work
and gives a list of the format specifiers. The default() and engine()
methods implement most of the below.

  Step 1 determines a table (T) and a path to a
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

    %c  evaluate children N[A] recursively*
    %C  evaluate children N[A[0]]..N[A[1]-1] recursively, separate by A[2]*
    %P  same as %C but sets operator precedence
    %D  same as %C but is for left-recursive lists like kwargs which
        goes to epsilon at the beginning. Using %C an extra separator
        with an epsilon appears at the beginning
    %,  print ',' if last %C only printed one item (for tuples--unused)
    %|  tab to current indentation level
    %+ increase current indentation level
    %- decrease current indentation level
    %{...} evaluate ... in context of N
    %% literal '%'
    %p evaluate N setting precedence


  * indicates an argument (A) required.

  The '%' may optionally be followed by a number (C) in square brackets, which
  makes the engine walk down to N[C] before evaluating the escape code.
"""
from __future__ import print_function

import sys, re

from uncompyle6 import PYTHON3
from uncompyle6.code import iscode
from uncompyle6.parser import get_python_parser
from uncompyle6.parsers.astnode import AST
from spark_parser import GenericASTTraversal, DEFAULT_DEBUG as PARSER_DEFAULT_DEBUG
from uncompyle6.scanner import Code, get_scanner
from uncompyle6.scanners.tok import Token, NoneToken
import uncompyle6.parser as python_parser

if PYTHON3:
    from itertools import zip_longest
    from io import StringIO
    minint = -sys.maxsize-1
    maxint = sys.maxsize
else:
    from itertools import izip_longest as zip_longest
    from StringIO import StringIO
    minint = -sys.maxint-1
    maxint = sys.maxint

# Some ASTs used for comparing code fragments (like 'return None' at
# the end of functions).

RETURN_LOCALS = AST('return_stmt',
                    [ AST('ret_expr', [AST('expr', [ Token('LOAD_LOCALS') ])]),
                      Token('RETURN_VALUE')])

NONE = AST('expr', [ NoneToken ] )

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

# TAB = '\t'			# as God intended
TAB = ' ' *4   # is less spacy than "\t"
INDENT_PER_LEVEL = ' ' # additional intent per pretty-print level

TABLE_R = {
    'STORE_ATTR':	( '%c.%[1]{pattr}', 0),
#   'STORE_SUBSCR':	( '%c[%c]', 0, 1 ),
    'DELETE_ATTR':	( '%|del %c.%[-1]{pattr}\n', 0 ),
#   'EXEC_STMT':	( '%|exec %c in %[1]C\n', 0, (0,maxint,', ') ),
}

if not PYTHON3:
    TABLE_R.update({
    'STORE_SLICE+0':	( '%c[:]', 0 ),
    'STORE_SLICE+1':	( '%c[%p:]', 0, (1, 100) ),
    'STORE_SLICE+2':	( '%c[:%p]', 0, (1, 100) ),
    'STORE_SLICE+3':	( '%c[%p:%p]', 0, (1, 100), (2, 100) ),
    'DELETE_SLICE+0':	( '%|del %c[:]\n', 0 ),
    'DELETE_SLICE+1':	( '%|del %c[%c:]\n', 0, 1 ),
    'DELETE_SLICE+2':	( '%|del %c[:%c]\n', 0, 1 ),
    'DELETE_SLICE+3':	( '%|del %c[%c:%c]\n', 0, 1, 2 ),
        })

TABLE_R0 = {
#    'BUILD_LIST':	( '[%C]',      (0,-1,', ') ),
#    'BUILD_TUPLE':	( '(%C)',      (0,-1,', ') ),
#    'CALL_FUNCTION':	( '%c(%P)', 0, (1,-1,', ') ),
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
    'slice1':		( '%c[%p:]', 0, (1, 100) ),
    'slice2':		( '%c[:%p]', 0, (1, 100) ),
    'slice3':		( '%c[%p:%p]', 0, (1, 100), (2, 100) ),

    'IMPORT_FROM':	( '%{pattr}', ),
    'load_attr':	( '%c.%[1]{pattr}', 0),
    'LOAD_FAST':	( '%{pattr}', ),
    'LOAD_NAME':	( '%{pattr}', ),
    'LOAD_CLASSNAME':	( '%{pattr}', ),
    'LOAD_GLOBAL':	( '%{pattr}', ),
    'LOAD_DEREF':	( '%{pattr}', ),
    'LOAD_LOCALS':	( 'locals()', ),
    'LOAD_ASSERT':  ( '%{pattr}', ),
#   'LOAD_CONST':	( '%{pattr}', ),	# handled by n_LOAD_CONST
    'DELETE_FAST':	( '%|del %{pattr}\n', ),
    'DELETE_NAME':	( '%|del %{pattr}\n', ),
    'DELETE_GLOBAL':	( '%|del %{pattr}\n', ),
    'delete_subscr':	( '%|del %c[%c]\n', 0, 1,),
    'binary_subscr':	( '%c[%p]', 0, (1, 100)),
    'binary_subscr2':	( '%c[%p]', 0, (1, 100)),
    'store_subscr':	( '%c[%c]', 0, 1),
    'STORE_FAST':	( '%{pattr}', ),
    'STORE_NAME':	( '%{pattr}', ),
    'STORE_GLOBAL':	( '%{pattr}', ),
    'STORE_DEREF':	( '%{pattr}', ),
    'unpack':		( '%C%,', (1, maxint, ', ') ),
    'unpack_w_parens':		( '(%C%,)', (1, maxint, ', ') ),
    'unpack_list':	( '[%C]', (1, maxint, ', ') ),
    'build_tuple2':	( '%P', (0, -1, ', ', 100) ),

    # 'list_compr':	( '[ %c ]', -2),	# handled by n_list_compr
    'list_iter':	( '%c', 0),
    'list_for':		( ' for %c in %c%c', 2, 0, 3 ),
    'list_if':		( ' if %c%c', 0, 2 ),
    'list_if_not':		( ' if not %p%c', (0, 22), 2 ),
    'lc_body':		( '', ),	# ignore when recusing

    'comp_iter':	( '%c', 0),
    'comp_for':		( ' for %c in %c%c', 2, 0, 3 ),
    'comp_if':		( ' if %c%c', 0, 2 ),
    'comp_ifnot':	( ' if not %p%c', (0, 22), 2 ),
    'comp_body':	( '', ),	# ignore when recusing
    'set_comp_body':    ( '%c', 0 ),
    'gen_comp_body':    ( '%c', 0 ),
    'dict_comp_body':   ( '%c:%c', 1, 0 ),

    'assign':		( '%|%c = %p\n', -1, (0, 200) ),
    'augassign1':	( '%|%c %c %c\n', 0, 2, 1),
    'augassign2':	( '%|%c.%[2]{pattr} %c %c\n', 0, -3, -4),
#   'dup_topx':		( '%c', 0),
    'designList':	( '%c = %c', 0, -1 ),
    'and':          	( '%c and %c', 0, 2 ),
    'ret_and':        	( '%c and %c', 0, 2 ),
    'and2':          	( '%c', 3 ),
    'or':           	( '%c or %c', 0, 2 ),
    'ret_or':           	( '%c or %c', 0, 2 ),
    'conditional':  ( '%p if %p else %p', (2, 27), (0, 27), (4, 27)),
    'ret_cond':     ( '%p if %p else %p', (2, 27), (0, 27), (4, 27)),
    'conditionalnot':  ( '%p if not %p else %p', (2, 27), (0, 22), (4, 27)),
    'ret_cond_not':  ( '%p if not %p else %p', (2, 27), (0, 22), (4, 27)),
    'conditional_lambda':  ( '(%c if %c else %c)', 2, 0, 3),
    'return_lambda':    ('%c', 0),
    'compare':		( '%p %[-1]{pattr} %p', (0, 19), (1, 19) ),
    'cmp_list':		( '%p %p', (0, 20), (1, 19)),
    'cmp_list1':	( '%[3]{pattr} %p %p', (0, 19), (-2, 19)),
    'cmp_list2':	( '%[1]{pattr} %p', (0, 19)),
#   'classdef': 	(), # handled by n_classdef()
    'funcdef':  	( '\n\n%|def %c\n', -2), # -2 to handle closures
    'funcdefdeco':  	( '\n\n%c', 0),
    'mkfuncdeco':  	( '%|@%c\n%c', 0, 1),
    'mkfuncdeco0':  	( '%|def %c\n', 0),
    'classdefdeco':  	( '\n\n%c', 0),
    'classdefdeco1':  	( '%|@%c\n%c', 0, 1),
    'kwarg':    	( '%[0]{pattr}=%c', 1),
    'kwargs':    	( '%D', (0, maxint, ', ') ),
    'importlist2':	( '%C', (0, maxint, ', ') ),

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

    'call_stmt':	( '%|%p\n', (0, 200)),
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
    'testtrue':     ( 'not %p', (0, 22) ),

    'ifelsestmt':	( '%|if %c:\n%+%c%-%|else:\n%+%c%-', 0, 1, 3 ),
    'ifelsestmtc':	( '%|if %c:\n%+%c%-%|else:\n%+%c%-', 0, 1, 3 ),
    'ifelsestmtl':	( '%|if %c:\n%+%c%-%|else:\n%+%c%-', 0, 1, 3 ),
    'ifelifstmt':	( '%|if %c:\n%+%c%-%c', 0, 1, 3 ),
    'elifelifstmt':	( '%|elif %c:\n%+%c%-%c', 0, 1, 3 ),
    'elifstmt':		( '%|elif %c:\n%+%c%-', 0, 1 ),
    'elifelsestmt':	( '%|elif %c:\n%+%c%-%|else:\n%+%c%-', 0, 1, 3 ),
    'ifelsestmtr':	( '%|if %c:\n%+%c%-%|else:\n%+%c%-', 0, 1, 2 ),
    'elifelsestmtr':	( '%|elif %c:\n%+%c%-%|else:\n%+%c%-\n\n', 0, 1, 2 ),

    'whileTruestmt':	( '%|while True:\n%+%c%-\n\n', 1 ),
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
    'except':                   ('%|except:\n%+%c%-', 3 ),
    'except_pop_except':        ('%|except:\n%+%c%-', 4 ),
    'except_cond1':	( '%|except %c:\n', 1 ),
    'except_cond2':	( '%|except %c as %c:\n', 1, 5 ),
    'except_suite':     ( '%+%c%-%C', 0, (1, maxint, '') ),
    'except_suite_finalize':     ( '%+%c%-%C', 1, (3, maxint, '') ),
    'tryfinallystmt':	( '%|try:\n%+%c%-%|finally:\n%+%c%-\n\n', 1, 5 ),
    'withstmt':     ( '%|with %c:\n%+%c%-', 0, 3),
    'withasstmt':   ( '%|with %c as %c:\n%+%c%-', 0, 2, 3),
    'passstmt':		( '%|pass\n', ),
    'STORE_FAST':	( '%{pattr}', ),
    'kv':		( '%c: %c', 3, 1 ),
    'kv2':		( '%c: %c', 1, 2 ),
    'mapexpr':		( '{%[1]C}', (0, maxint, ', ') ),

    #######################
    # Python 2.5 Additions
    #######################

    # Import style for 2.5
    'importstmt': ( '%|import %c\n', 2),
    'importstar': ( '%|from %[2]{pattr} import *\n', ),
    'importfrom': ( '%|from %[2]{pattr} import %c\n', 3 ),
    'importmultiple': ( '%|import %c%c\n', 2, 3 ),
    'import_cont'   : ( ', %c', 2 ),

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

def is_docstring(node):
    try:
        return (node[0][0].type == 'assign' and
            node[0][0][1][0].pattr == '__doc__')
    except:
        return False

class ParserError(python_parser.ParserError):
    def __init__(self, error, tokens):
        self.error = error # previous exception
        self.tokens = tokens

    def __str__(self):
        lines = ['--- This code section failed: ---']
        lines.extend( list(map(str, self.tokens)) )
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
        elif n.type == 'LOAD_CONST' and n.pattr is None:
            return True
    return False

class SourceWalkerError(Exception):
    def __init__(self, errmsg):
        self.errmsg = errmsg

    def __str__(self):
        return self.errmsg

class SourceWalker(GenericASTTraversal, object):
    stacked_params = ('f', 'indent', 'isLambda', '_globals')

    def __init__(self, version, out, scanner, showast=False,
                 debug_parser=PARSER_DEFAULT_DEBUG,
                 compile_mode='exec'):
        GenericASTTraversal.__init__(self, ast=None)
        self.scanner = scanner
        params = {
            'f': out,
            'indent': '',
            }
        self.version = version
        self.p = get_python_parser(version, debug_parser=debug_parser,
                                   compile_mode=compile_mode)
        self.debug_parser = dict(debug_parser)
        self.showast = showast
        self.params = params
        self.param_stack = []
        self.ERROR = None
        self.prec = 100
        self.return_none = False
        self.mod_globs = set()
        self.currentclass = None
        self.classes = []
        self.pending_newlines = 0
        self.hide_internal = True

        return

    f = property(lambda s: s.params['f'],
                 lambda s, x: s.params.__setitem__('f', x),
                 lambda s: s.params.__delitem__('f'),
                 None)

    indent = property(lambda s: s.params['indent'],
                 lambda s, x: s.params.__setitem__('indent', x),
                 lambda s: s.params.__delitem__('indent'),
                 None)

    isLambda = property(lambda s: s.params['isLambda'],
                 lambda s, x: s.params.__setitem__('isLambda', x),
                 lambda s: s.params.__delitem__('isLambda'),
                 None)

    _globals = property(lambda s: s.params['_globals'],
                 lambda s, x: s.params.__setitem__('_globals', x),
                 lambda s: s.params.__delitem__('_globals'),
                 None)

    def indentMore(self, indent=TAB):
        self.indent += indent

    def indentLess(self, indent=TAB):
        self.indent = self.indent[:-len(indent)]

    def traverse(self, node, indent=None, isLambda=0):
        self.param_stack.append(self.params)
        if indent is None: indent = self.indent
        p = self.pending_newlines
        self.pending_newlines = 0
        self.params = {
            '_globals': {},
            'f': StringIO(),
            'indent': indent,
            'isLambda': isLambda,
            }
        self.preorder(node)
        self.f.write('\n'*self.pending_newlines)
        result = self.f.getvalue()
        self.params = self.param_stack.pop()
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

    def println(self, *data):
        if data and not(len(data) == 1 and data[0] ==''):
            self.write(*data)
        self.pending_newlines = max(self.pending_newlines, 1)

    def print_docstring(self, indent, docstring):
        quote = '"""'
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
            # Escape triple quote anywhere
            docstring = docstring.replace('"""', '\\"\\"\\"')
            # Restore escaped backslashes
            docstring = docstring.replace('\t', '\\\\')
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

    def n_return_stmt(self, node):
        if self.params['isLambda']:
            self.preorder(node[0])
            self.prune()
        else:
            self.write(self.indent, 'return')
            if self.return_none or node != AST('return_stmt', [AST('ret_expr', [NONE]), Token('RETURN_VALUE')]):
                self.write(' ')
                self.preorder(node[0])
            self.println()
            self.prune() # stop recursing

    def n_return_if_stmt(self, node):
        if self.params['isLambda']:
            self.preorder(node[0])
            self.prune()
        else:
            self.write(self.indent, 'return')
            if self.return_none or node != AST('return_stmt', [AST('ret_expr', [NONE]), Token('RETURN_END_IF')]):
                self.write(' ')
                self.preorder(node[0])
            self.println()
            self.prune() # stop recursing

    def n_yield(self, node):
        self.write('yield')
        if node != AST('yield', [NONE, Token('YIELD_VALUE')]):
            self.write(' ')
            self.preorder(node[0])
        self.prune() # stop recursing

    # In Python 3.3+ only
    def n_yield_from(self, node):
        self.write('yield from')
        self.write(' ')
        self.preorder(node[0][0][0][0])
        self.prune() # stop recursing

    def n_buildslice3(self, node):
        p = self.prec
        self.prec = 100
        if not node[0].isNone():
            self.preorder(node[0])
        self.write(':')
        if not node[1].isNone():
            self.preorder(node[1])
        self.write(':')
        if not node[2].isNone():
            self.preorder(node[2])
        self.prec = p
        self.prune() # stop recursing

    def n_buildslice2(self, node):
        p = self.prec
        self.prec = 100
        if not node[0].isNone():
            self.preorder(node[0])
        self.write(':')
        if not node[1].isNone():
            self.preorder(node[1])
        self.prec = p
        self.prune() # stop recursing

    def n_expr(self, node):
        p = self.prec
        if node[0].type.startswith('binary_expr'):
            n = node[0][-1][0]
        else:
            n = node[0]

        self.prec = PRECEDENCE.get(n.type, -2)
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
        if isinstance(datatype, int) and data == minint:
            # convert to hex, since decimal representation
            # would result in 'LOAD_CONST; UNARY_NEGATIVE'
            # change:hG/2002-02-07: this was done for all negative integers
            # todo: check whether this is necessary in Python 2.1
            self.write( hex(data) )
        elif datatype is type(Ellipsis):
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
        if not node[1][0].isNone():
            sep = ' in '
            for subnode in node[1]:
                self.write(sep); sep = ", "
                self.preorder(subnode)
        self.println()
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
        self.println(':')
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
                    self.println(self.indent, 'else:')
                    self.indentMore()
                    past_else = True
            self.preorder(n)
        if not past_else or if_ret_at_end:
            self.println(self.indent, 'else:')
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
        self.println(':')
        self.indentMore()
        self.preorder(node[1])
        self.indentLess()

        for n in node[2][0]:
            n[0].type = 'elifstmt'
            self.preorder(n)
        self.println(self.indent, 'else:')
        self.indentMore()
        self.preorder(node[2][1])
        self.indentLess()
        self.prune()

    def n_import_as(self, node):
        iname = node[0].pattr
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

        if self.version >= 3.3:
            # LOAD_CONST code object ..
            # LOAD_CONST        'x0'
            # MAKE_FUNCTION ..
            code_index = -3
        else:
            # LOAD_CONST code object ..
            # MAKE_FUNCTION ..
            code_index = -2
        code = node[code_index]
        func_name = code.attr.co_name
        self.write(func_name)

        self.indentMore()
        self.make_function(node, isLambda=False, code_index=code_index)

        if len(self.param_stack) > 1:
            self.write('\n\n')
        else:
            self.write('\n\n\n')
        self.indentLess()
        self.prune() # stop recursing

    def n_mklambda(self, node):
        self.make_function(node, isLambda=True)
        self.prune() # stop recursing

    def n_list_compr(self, node):
        """List comprehensions the way they are done in Python2.
        """
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
        self.write( '[ ')
        self.preorder(n[0]) # lc_body
        self.preorder(node[-1]) # for/if parts
        self.write( ' ]')
        self.prec = p
        self.prune() # stop recursing

    def comprehension_walk(self, node, iter_index, code_index=-5):
        p = self.prec
        self.prec = 27
        if hasattr(node[code_index], 'attr'):
            # Python 2.5+ (and earlier?) does this
            code = node[code_index].attr
        else:
            if len(node[1]) > 1 and hasattr(node[1][1], 'attr'):
                # Python 3.3+ does this
                code = node[1][1].attr
            elif hasattr(node[1][0], 'attr'):
                # Python 3.2 does this
                code = node[1][0].attr
            else:
                assert False, "Can't find code for comprehension"

        assert iscode(code)
        code = Code(code, self.scanner, self.currentclass)
        ast = self.build_ast(code._tokens, code._customize)
        self.customize(code._customize)
        ast = ast[0][0][0]

        n = ast[iter_index]
        assert n == 'comp_iter'
        # find innerst node
        while n == 'comp_iter': # list_iter
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
        code_index = -6 if self.version > 3.0 else -5
        self.comprehension_walk(node, iter_index=3, code_index=code_index)
        self.write(')')
        self.prune()

    def n_setcomp(self, node):
        self.write('{')
        self.comprehension_walk(node, iter_index=4)
        self.write('}')
        self.prune()

    def listcomprehension_walk3(self, node, iter_index, code_index=-5):
        """
        List comprehensions the way they are done in Python3.
        They're more other comprehensions, e.g. set comprehensions
        See if we can combine code.
        """
        p = self.prec
        self.prec = 27
        code = node[code_index].attr

        assert iscode(code)
        code = Code(code, self.scanner, self.currentclass)

        ast = self.build_ast(code._tokens, code._customize)
        self.customize(code._customize)
        ast = ast[0][0][0][0][0]

        n = ast[iter_index]
        assert n == 'list_iter'

        # find innermost node
        while n == 'list_iter':
            n = n[0] # recurse one step
            if   n == 'list_for':
                designator = n[2]
                n = n[3]
            elif n in ['list_if', 'list_if_not']:
                # FIXME: just a guess
                designator = n[1]
                n = n[2]
                pass
            pass
        assert n == 'lc_body', ast

        self.preorder(n[0])
        self.write(' for ')
        self.preorder(designator)
        self.write(' in ')
        self.preorder(node[-3])
        self.prec = p

    def listcomprehension_walk2(self, node):
        """List comprehensions the way they are done in Python3.
        They're more other comprehensions, e.g. set comprehensions
        See if we can combine code.
        """
        p = self.prec
        self.prec = 27

        code = Code(node[1].attr, self.scanner, self.currentclass)
        ast = self.build_ast(code._tokens, code._customize)
        self.customize(code._customize)
        ast = ast[0][0][0][0][0]

        n = ast[1]
        collection = node[-3]
        list_if = None
        assert n == 'list_iter'

        # find innermost node
        while n == 'list_iter':
            n = n[0] # recurse one step
            if   n == 'list_for':
                designator = n[2]
                n = n[3]
            elif n in ('list_if', 'list_if_not'):
                # FIXME: just a guess
                if n[0].type == 'expr':
                    list_if = n
                else:
                    list_if = n[1]
                n = n[2]
                pass
            pass

        assert n == 'lc_body', ast

        self.preorder(n[0])
        self.write(' for ')
        self.preorder(designator)
        self.write(' in ')
        self.preorder(collection)
        if list_if:
            self.preorder(list_if)
        self.prec = p

    def n_listcomp(self, node):
        self.write('[')
        if node[0].type == 'load_closure':
            self.listcomprehension_walk2(node)
        else:
            self.listcomprehension_walk3(node, 1, 0)
        self.write(']')
        self.prune()

    n_dictcomp = n_setcomp

    def n_classdef(self, node):
        # class definition ('class X(A,B,C):')
        cclass = self.currentclass

        if self.version > 3.0:
            currentclass = node[1][0].pattr
            buildclass = node[0]
            if buildclass[1][0] == 'kwargs':
                subclass = buildclass[1][1].attr
                subclass_info = node[0]
            elif buildclass[1][0] == 'load_closure':
                # Python 3 with closures not functions
                load_closure = buildclass[1]
                if hasattr(load_closure[-3], 'attr'):
                    # Python 3.3 classes with closures work like this.
                    # Note have to test before 3.2 case because
                    # index -2 also has an attr.
                    subclass = load_closure[-3].attr
                elif hasattr(load_closure[-2], 'attr'):
                    # Python 3.2 works like this
                    subclass = load_closure[-2].attr
                else:
                    raise 'Internal Error n_classdef: cannot find class body'
                if hasattr(buildclass[3], '__len__'):
                    subclass_info = buildclass[3]
                elif hasattr(buildclass[2], '__len__'):
                    subclass_info = buildclass[2]
                else:
                    raise 'Internal Error n_classdef: cannot superclass name'
            else:
                subclass = buildclass[1][0].attr
                subclass_info = node[0]
        else:
            buildclass = node if (node == 'classdefdeco2') else node[0]
            build_list = buildclass[1][0]
            if hasattr(buildclass[-3][0], 'attr'):
                subclass = buildclass[-3][0].attr
                currentclass = buildclass[0].pattr
            elif hasattr(node[0][0], 'pattr'):
                subclass = buildclass[-3][1].attr
                currentclass = node[0][0].pattr
            else:
                raise 'Internal Error n_classdef: cannot find class name'

        if (node == 'classdefdeco2'):
            self.write('\n')
        else:
            self.write('\n\n')

        self.currentclass = str(currentclass)
        self.write(self.indent, 'class ', self.currentclass)

        if self.version > 3.0:
            self.print_super_classes3(subclass_info)
        else:
            self.print_super_classes(build_list)
        self.println(':')

        # class body
        self.indentMore()
        self.build_class(subclass)
        self.indentLess()

        self.currentclass = cclass
        if len(self.param_stack) > 1:
            self.write('\n\n')
        else:
            self.write('\n\n\n')

        self.prune()

    n_classdefdeco2 = n_classdef

    def print_super_classes(self, node):
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

    def print_super_classes3(self, node):
        n = len(node)-1
        if node.type != 'expr':
            assert node[n].type.startswith('CALL_FUNCTION')
            for i in range(n-2, 0, -1):
                if not node[i].type in ['expr', 'LOAD_CLASSNAME']:
                    break
                pass

            if i == n-2:
                return
            line_separator = ', '
            sep = ''
            self.write('(')
            i += 2
            while i < n:
                value = self.traverse(node[i])
                i += 1
                self.write(sep, value)
                sep = line_separator
                pass
            pass
        else:
            self.write('(')
            value = self.traverse(node[0])
            self.write(value)
            pass

        self.write(')')

    def n_mapexpr(self, node):
        """
        prettyprint a mapexpr
        'mapexpr' is something like k = {'a': 1, 'b': 42 }"
        """
        p = self.prec
        self.prec = 100

        self.indentMore(INDENT_PER_LEVEL)
        line_seperator = ',\n' + self.indent
        sep = INDENT_PER_LEVEL[:-1]
        self.write('{')

        if self.version > 3.0:
            if node[0].type.startswith('kvlist'):
                # Python 3.5+ style key/value list in mapexpr
                kv_node = node[0]
                l = list(kv_node)
                i = 0
                while i < len(l):
                    name = self.traverse(l[i], indent='')
                    value = self.traverse(l[i+1], indent=self.indent+(len(name)+2)*' ')
                    self.write(sep, name, ': ', value)
                    sep = line_seperator
                    i += 2
                    pass
                pass
            elif node[1].type.startswith('kvlist'):
                # Python 3.0..3.4 style key/value list in mapexpr
                kv_node = node[1]
                l = list(kv_node)
                if len(l) > 0 and l[0].type == 'kv3':
                    # Python 3.2 does this
                    kv_node = node[1][0]
                    l = list(kv_node)
                i = 0
                while i < len(l):
                    try:
                        name = self.traverse(l[i+1], indent='')
                    except:
                        from trepan.api import debug; debug()
                    value = self.traverse(l[i], indent=self.indent+(len(name)+2)*' ')
                    self.write(sep, name, ': ', value)
                    sep = line_seperator
                    i += 3
                    pass
                pass
            pass
        else:
            # Python 2 style kvlist
            assert node[-1] == 'kvlist'
            kv_node = node[-1] # goto kvlist

            for kv in kv_node:
                assert kv in ('kv', 'kv2', 'kv3')
                # kv ::= DUP_TOP expr ROT_TWO expr STORE_SUBSCR
                # kv2 ::= DUP_TOP expr expr ROT_THREE STORE_SUBSCR
                # kv3 ::= expr expr STORE_MAP
                if kv == 'kv':
                    name = self.traverse(kv[-2], indent='')
                    value = self.traverse(kv[1], indent=self.indent+(len(name)+2)*' ')
                elif kv == 'kv2':
                    name = self.traverse(kv[1], indent='')
                    value = self.traverse(kv[-3], indent=self.indent+(len(name)+2)*' ')
                elif kv == 'kv3':
                    name = self.traverse(kv[-2], indent='')
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
        lastnode = node.pop()
        lastnodetype = lastnode.type
        if lastnodetype.startswith('BUILD_LIST'):
            self.write('['); endchar = ']'
        elif lastnodetype.startswith('BUILD_TUPLE'):
            self.write('('); endchar = ')'
        elif lastnodetype.startswith('BUILD_SET'):
            self.write('{'); endchar = '}'
        elif lastnodetype.startswith('ROT_TWO'):
            self.write('('); endchar = ')'
        else:
            raise 'Internal Error: n_build_list expects list or tuple'

        flat_elems = []
        for elem in node:
            if elem == 'expr1024':
                for subelem in elem:
                        for subsubelem in subelem:
                            flat_elems.append(subsubelem)
            elif elem == 'expr32':
                for subelem in elem:
                    flat_elems.append(subelem)
            else:
                flat_elems.append(elem)

        self.indentMore(INDENT_PER_LEVEL)
        if lastnode.attr > 3:
            line_separator = ',\n' + self.indent
        else:
            line_separator = ', '
        sep = INDENT_PER_LEVEL[:-1]

        # FIXME:
        # if flat_elems > some_number, then group
        # do automatic wrapping
        for elem in flat_elems:
            if elem == 'ROT_THREE':
                continue
            assert elem == 'expr'
            value = self.traverse(elem)
            self.write(sep, value)
            sep = line_separator
        if lastnode.attr == 1 and lastnodetype.startswith('BUILD_TUPLE'):
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

    def n_assign(self, node):
        # A horrible hack for Python 3.0 .. 3.2
        if 3.0 <= self.version <= 3.2 and len(node) == 2:
            if (node[0][0] == 'LOAD_FAST' and node[0][0].pattr == '__locals__' and
                node[1][0].type == 'STORE_LOCALS'):
                self.prune()
        self.default(node)

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
        """The format template interpetation engine.  See the comment at the
        beginning of this module for the how we interpret format specifications such as
        %c, %C, and so on.
        """

        # self.println("-----")
        # self.print(startnode)

        fmt = entry[0]
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
                print(node.__dict__)
                raise

            if   typ == '%':	self.write('%')
            elif typ == '+':	self.indentMore()
            elif typ == '-':	self.indentLess()
            elif typ == '|':	self.write(self.indent)
            # no longer used, since BUILD_TUPLE_n is pretty printed:
            elif typ == ',':
                pass
            elif typ == 'c':
                # FIXME: In Python3 sometimes like from
                # importfrom
                #   importlist2
                #     import_as
                #       designator
                # STORE_NAME        'load_entry_point'
                #	POP_TOP           '' (2, (0, 1))
                # we get that weird POP_TOP tuple, e.g (2, (0,1)).
                # Why? and
                # Is there some sort of invalid bounds access going on?
                if isinstance(entry[arg], int):
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
                remaining = len(node[low:high])
                # remaining = len(node[low:high])
                for subnode in node[low:high]:
                    self.preorder(subnode)
                    remaining -= 1
                    if remaining > 0:
                        self.write(sep)
                arg += 1
            elif typ == 'D':
                low, high, sep = entry[arg]
                remaining = len(node[low:high])
                for subnode in node[low:high]:
                    remaining -= 1
                    if len(subnode) > 0:
                        self.preorder(subnode)
                        if remaining > 0:
                            self.write(sep)
                            pass
                        pass
                    pass
                arg += 1
            elif typ == 'P':
                p = self.prec
                low, high, sep, self.prec = entry[arg]
                remaining = len(node[low:high])
                # remaining = len(node[low:high])
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
                    print(node)
                    raise
            m = escape.search(fmt, i)
        self.write(fmt[i:])

    def default(self, node):
        mapping = MAP.get(node, MAP_DIRECT)
        table = mapping[0]
        key = node

        for i in mapping[1:]:
            key = key[i]
            pass

        if key.type in table:
            self.engine(table[key.type], node)
            self.prune()

    def customize(self, customize):
        """
        Special handling for opcodes that take a variable number
        of arguments -- we add a new entry for each in TABLE_R.
        """
        for k, v in list(customize.items()):
            if k in TABLE_R:
                continue
            op = k[ :k.rfind('_') ]
            if op == 'CALL_FUNCTION':
                TABLE_R[k] = ('%c(%P)', 0, (1, -1, ', ', 100))
            elif op in ('CALL_FUNCTION_VAR',
                        'CALL_FUNCTION_VAR_KW', 'CALL_FUNCTION_KW'):
                if v == 0:
                    str = '%c(%C' # '%C' is a dummy here ...
                    p2 = (0, 0, None) # .. because of this
                else:
                    str = '%c(%C, '
                    p2 = (1, -2, ', ')
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
                    pass
                TABLE_R[k] = entry
                pass
            # handled by n_mapexpr:
            # if op == 'BUILD_SLICE':	TABLE_R[k] = ('%C'    ,    (0,-1,':'))
            # handled by n_build_list:
            # if   op == 'BUILD_LIST':	TABLE_R[k] = ('[%C]'  ,    (0,-1,', '))
            # elif op == 'BUILD_TUPLE':	TABLE_R[k] = ('(%C%,)',    (0,-1,', '))
            pass
        return

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
            if (node == 'assign'
                and node[0] == ASSIGN_TUPLE_PARAM(name)):
                # okay, this assigns '.n' to something
                del ast[i]
                # walk lhs; this
                # returns a tuple of identifiers as used
                # within the function definition
                assert node[1] == 'designator'
                # if lhs is not a UNPACK_TUPLE (or equiv.),
                # add parenteses to make this a tuple
                # if node[1][0] not in ('unpack', 'unpack_list'):
                return '(' + self.traverse(node[1]) + ')'
            # return self.traverse(node[1])
        raise Exception("Can't find tuple parameter " + name)

    def make_function(self, node, isLambda, nested=1, code_index=-2):
        """Dump function defintion, doc string, and function body."""

        def build_param(ast, name, default):
            """build parameters:
                - handle defaults
                - handle format tuple parameters
            """
            if self.version < 3.0:
                # if formal parameter is a tuple, the paramater name
                # starts with a dot (eg. '.1', '.2')
                if name.startswith('.'):
                    # replace the name with the tuple-string
                    name = self.get_tuple_parameter(ast, name)
                    pass
                pass

            if default:
                if self.showast:
                    print()
                    print('--', name)
                    print(default)
                    print('--')
                result = '%s=%s' % (name, self.traverse(default, indent='') )
                if result[-2:] == '= ':	# default was 'LOAD_CONST None'
                    result += 'None'
                return result
            else:
                return name

        # node[-1] == MAKE_FUNCTION_n

        args_node = node[-1]
        if isinstance(args_node.attr, tuple):
            defparams = node[:args_node.attr[0]]
            pos_args, kw_args, annotate_args  = args_node.attr
        else:
            defparams = node[:args_node.attr]
            kw_args, annotate_args  = (0, 0)
            pos_args = args_node.attr
            pass

        if self.version > 3.0 and isLambda and iscode(node[-3].attr):
            code = node[-3].attr
        else:
            code = node[code_index].attr

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

        # build parameters

        params = [build_param(ast, name, default) for
                  name, default in zip_longest(paramnames, defparams, fillvalue=None)]

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
            self.write("lambda ", ", ".join(params))
        else:
            self.write("(", ", ".join(params))
            # self.println(indent, '#flags:\t', int(code.co_flags))

        if kw_args > 0:
            if argc > 0:
                self.write(", *, ")
            else:
                self.write("*, ")
            for n in node:
                if n == 'pos_arg':
                    continue
                self.preorder(n)
                break
            pass

        if isLambda:
            self.write(": ")
        else:
            self.println("):")

        if len(code.co_consts)>0 and code.co_consts[0] is not None and not isLambda: # ugly
            # docstring exists, dump it
            self.print_docstring(indent, code.co_consts[0])

        code._tokens = None # save memory
        assert ast == 'stmts'

        all_globals = find_all_globals(ast, set())
        for g in ((all_globals & self.mod_globs) | find_globals(ast, set())):
            self.println(self.indent, 'global ', g)
        self.mod_globs -= all_globals
        rn = ('None' in code.co_names) and not find_none(ast)
        self.gen_source(ast, code.co_name, code._customize, isLambda=isLambda,
                            returnNone=rn)
        code._tokens = None; code._customize = None # save memory

    def build_class(self, code):
        """Dump class definition, doc string and class body."""

        assert iscode(code)
        self.classes.append(self.currentclass)
        code = Code(code, self.scanner, self.currentclass)

        indent = self.indent
        # self.println(indent, '#flags:\t', int(code.co_flags))
        ast = self.build_ast(code._tokens, code._customize)
        code._tokens = None # save memory
        assert ast == 'stmts'

        try:
            if ast[0][0] == NAME_MODULE:
                if self.hide_internal: del ast[0]
            elif ast[1][0] == NAME_MODULE:
                if self.hide_internal: del ast[1]
            pass
        except:
            pass

        qualname = '.'.join(self.classes)

        QUAL_NAME = AST('stmt',
                    [ AST('assign',
                        [ AST('expr', [Token('LOAD_CONST', pattr=qualname)]),
                        AST('designator', [ Token('STORE_NAME', pattr='__qualname__')])
                        ])])
        if ast[0][0] == QUAL_NAME:
            if self.hide_internal: del ast[0]
            pass

        # if docstring exists, dump it
        if (code.co_consts and code.co_consts[0] is not None and len(ast) > 0):
            do_doc = False
            if is_docstring(ast[0]):
                i = 0
                do_doc = True
            elif (len(ast) > 1 and is_docstring(ast[1])):
                i = 1
                do_doc = True
            if do_doc and self.hide_internal:
                try:
                    docstring = ast[i][0][0][0][0].pattr
                except:
                    docstring = code.co_consts[0]
                self.print_docstring(indent, docstring)
                self.println()
                del ast[i]


        # the function defining a class normally returns locals(); we
        # don't want this to show up in the source, thus remove the node
        if len(ast) > 0 and ast[-1][0] == RETURN_LOCALS:
            if self.hide_internal: del ast[-1] # remove last node
        # else:
        #    print ast[-1][-1]

        for g in find_globals(ast, set()):
            self.println(indent, 'global ', g)

        self.gen_source(ast, code.co_name, code._customize)
        code._tokens = None; code._customize = None # save memory
        self.classes.pop(-1)

    def gen_source(self, ast, name, customize, isLambda=False, returnNone=False):
        """convert AST to source code"""

        rn = self.return_none
        self.return_none = returnNone
        self.name = name
        # if code would be empty, append 'pass'
        if len(ast) == 0:
            self.println(self.indent, 'pass')
        else:
            self.customize(customize)
            if isLambda:
                self.write(self.traverse(ast, isLambda=isLambda))
            else:
                self.text = self.traverse(ast, isLambda=isLambda)
                self.println(self.text)
        self.return_none = rn

    def build_ast(self, tokens, customize, isLambda=0, noneInNames=False):

        # assert isinstance(tokens[0], Token)

        if isLambda:
            tokens.append(Token('LAMBDA_MARKER'))
            try:
                ast = python_parser.parse(self.p, tokens, customize)
            except (python_parser.ParserError, AssertionError) as e:
                raise ParserError(e, tokens)
            if self.showast:
                self.println(repr(ast))
            return ast

        # The bytecode for the end of the main routine has a
        # "return None". However you can't issue a "return" statement in
        # main. So as the old cigarette slogan goes: I'd rather switch (the token stream)
        # than fight (with the grammar to not emit "return None").
        if self.hide_internal:
            if len(tokens) >= 2 and not noneInNames:
                if tokens[-1].type == 'RETURN_VALUE':
                    if tokens[-2].type == 'LOAD_CONST':
                        del tokens[-2:]
                    else:
                        tokens.append(Token('RETURN_LAST'))
            if len(tokens) == 0:
                return PASS

        # Build AST from disassembly.
        try:
            ast = python_parser.parse(self.p, tokens, customize)
        except (python_parser.ParserError, AssertionError) as e:
            raise ParserError(e, tokens)

        if self.showast:
            self.println(repr(ast))

        return ast

def deparse_code(version, co, out=sys.stdout, showasm=False, showast=False,
                 showgrammar=False, code_objects={}, compile_mode='exec'):
    """
    disassembles and deparses a given code block 'co'
    """

    assert iscode(co)
    # store final output stream for case of error
    scanner = get_scanner(version)

    tokens, customize = scanner.disassemble(co, code_objects=code_objects)
    if showasm:
        for t in tokens:
            print(t)

    debug_parser = dict(PARSER_DEFAULT_DEBUG)
    if showgrammar:
        debug_parser['reduce'] = showgrammar
        debug_parser['errorstack'] = True

    #  Build AST from disassembly.
    deparsed = SourceWalker(version, out, scanner, showast=showast,
                            debug_parser=debug_parser, compile_mode=compile_mode)

    deparsed.ast = deparsed.build_ast(tokens, customize)

    assert deparsed.ast == 'stmts', 'Should have parsed grammar start'

    del tokens # save memory

    deparsed.mod_globs = find_globals(deparsed.ast, set())

    # convert leading '__doc__ = "..." into doc string
    try:
        if deparsed.ast[0][0] == ASSIGN_DOC_STRING(co.co_consts[0]):
            deparsed.print_docstring('', co.co_consts[0])
            del deparsed.ast[0]
        if deparsed.ast[-1] == RETURN_NONE:
            deparsed.ast.pop() # remove last node
            # todo: if empty, add 'pass'
    except:
        pass

    # What we've been waiting for: Generate source from AST!
    deparsed.gen_source(deparsed.ast, co.co_name, customize)

    for g in deparsed.mod_globs:
        deparsed.write('# global %s ## Warning: Unused global' % g)

    if deparsed.ERROR:
        raise SourceWalkerError("Deparsing stopped due to parse error")
    return deparsed

if __name__ == '__main__':
    def deparse_test(co):
        "This is a docstring"
        sys_version = sys.version_info.major + (sys.version_info.minor / 10.0)
        deparsed = deparse_code(sys_version, co, showasm=True, showast=True)
        # deparsed = deparse_code(sys_version, co, showasm=False, showast=False,
        #                         showgrammar=True)
        print(deparsed.text)
        return
    deparse_test(deparse_test.__code__)
