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
of the nonterminal is suffixed with "_exit" it will be called after
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
    %,  print ',' if last %C only printed one item. This is mostly for tuples
        on the LHS of an assignment statement since BUILD_TUPLE_n pretty-prints
        other tuples.
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
import sys, re

from uncompyle6 import PYTHON3
from xdis.code import iscode
from uncompyle6.parser import get_python_parser
from uncompyle6.parsers.astnode import AST
from spark_parser import GenericASTTraversal, DEFAULT_DEBUG as PARSER_DEFAULT_DEBUG
from uncompyle6.scanner import Code, get_scanner
from uncompyle6.scanners.tok import Token, NoneToken
import uncompyle6.parser as python_parser
from uncompyle6.semantics.make_function import (
    make_function2, make_function3, make_function3_annotate, find_globals)
from uncompyle6.semantics.parser_error import ParserError
from uncompyle6.semantics.check_ast import checker
from uncompyle6.semantics.helper import print_docstring

from uncompyle6.show import (
    maybe_show_ast,
)

if PYTHON3:
    from io import StringIO
    minint = -sys.maxsize-1
    maxint = sys.maxsize
else:
    from StringIO import StringIO
    minint = -sys.maxint-1
    maxint = sys.maxint

LINE_LENGTH = 80

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
                    [ AST('expr',
                          [Token('LOAD_NAME', pattr='__name__', offset=0, has_arg=True)]),
                      AST('designator',
                          [ Token('STORE_NAME', pattr='__module__', offset=3, has_arg=True)])
                      ])])

# God intended \t, but Python has decided to use 4 spaces.
# If you want real tabs, use Go.
# TAB = '\t'
TAB = ' ' * 4
INDENT_PER_LEVEL = ' ' # additional intent per pretty-print level

TABLE_R = {
    'STORE_ATTR':	( '%c.%[1]{pattr}', 0),
#   'STORE_SUBSCR':	( '%c[%c]', 0, 1 ),
    'DELETE_ATTR':	( '%|del %c.%[-1]{pattr}\n', 0 ),
#   'EXEC_STMT':	( '%|exec %c in %[1]C\n', 0, (0,maxint,', ') ),
}

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
    'BINARY_MATRIX_MULTIPLY':	( '@' ,),
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
    'INPLACE_MATRIX_MULTIPLY':	( '@=' ,),
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

    # This nonterminal we create on the fly in semantic routines
    'unpack_w_parens':	( '(%C%,)', (1, maxint, ', ') ),

    'unpack_list':	( '[%C]', (1, maxint, ', ') ),
    'build_tuple2':	( '%P', (0, -1, ', ', 100) ),

    # 'list_compr':	( '[ %c ]', -2),	# handled by n_list_compr
    'list_iter':	( '%c', 0),
    'list_for':		( ' for %c in %c%c', 2, 0, 3 ),
    'list_if':		( ' if %c%c', 0, 2 ),
    'list_if_not':		( ' if not %p%c', (0, 22), 2 ),
    'lc_body':		( '', ),	# ignore when recusing

    'comp_iter':	( '%c', 0),
    'comp_if':		( ' if %c%c', 0, 2 ),
    'comp_ifnot':	( ' if not %p%c', (0, 22), 2 ),
    'comp_body':	( '', ),	# ignore when recusing
    'set_comp_body':    ( '%c', 0 ),
    'gen_comp_body':    ( '%c', 0 ),
    'dict_comp_body':   ( '%c:%c', 1, 0 ),

    'assign':		( '%|%c = %p\n', -1, (0, 200) ),

    # The 2nd parameter should have a = suffix.
    # There is a rule with a 4th parameter "designator"
    # which we don't use here.
    'augassign1':	( '%|%c %c %c\n', 0, 2, 1),

    'augassign2':	( '%|%c.%[2]{pattr} %c %c\n', 0, -3, -4),
    'designList':	( '%c = %c', 0, -1 ),
    'and':          	( '%c and %c', 0, 2 ),
    'ret_and':        	( '%c and %c', 0, 2 ),
    'and2':          	( '%c', 3 ),
    'or':           	( '%c or %c', 0, 2 ),
    'ret_or':           	( '%c or %c', 0, 2 ),
    'conditional':  ( '%p if %p else %p', (2, 27), (0, 27), (4, 27)),
    'ret_cond':     ( '%p if %p else %p', (2, 27), (0, 27), (-1, 27)),
    'conditionalnot':  ( '%p if not %p else %p', (2, 27), (0, 22), (4, 27)),
    'ret_cond_not':  ( '%p if not %p else %p', (2, 27), (0, 22), (-1, 27)),
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

    'assert_expr_or': ( '%c or %c', 0, 2 ),
    'assert_expr_and':    ( '%c and %c', 0, 2 ),
    'print_items_stmt': ( '%|print %c%c,\n', 0, 2),  # Python 2 only
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
    'raise_stmt3':	( '%|raise %c, %c, %c\n', 0, 1, 2),
#    'yield':	( 'yield %c', 0),
#    'return_stmt':	( '%|return %c\n', 0),

    'ifstmt':		( '%|if %c:\n%+%c%-', 0, 1 ),
    'iflaststmt':		( '%|if %c:\n%+%c%-', 0, 1 ),
    'iflaststmtl':		( '%|if %c:\n%+%c%-', 0, 1 ),
    'testtrue':         ( 'not %p', (0, 22) ),

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
    'while1elsestmt':  ( '%|while 1:\n%+%c%-%|else:\n%+%c%-\n\n', 1, -2 ),
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
    'tryelsestmt':	( '%|try:\n%+%c%-%c%|else:\n%+%c%-\n\n', 1, 3, 4 ),
    'tryelsestmtc':	( '%|try:\n%+%c%-%c%|else:\n%+%c%-', 1, 3, 4 ),
    'tryelsestmtl':	( '%|try:\n%+%c%-%c%|else:\n%+%c%-', 1, 3, 4 ),
    'tf_trystmt':	( '%c%-%c%+', 1, 3 ),
    'tf_tryelsestmt':	( '%c%-%c%|else:\n%+%c', 1, 3, 4 ),
    'tryfinallystmt':	( '%|try:\n%+%c%-%|finally:\n%+%c%-\n\n', 1, 5 ),
    'except':           ( '%|except:\n%+%c%-', 3 ),
    'except_cond1':	( '%|except %c:\n', 1 ),
    'except_suite':     ( '%+%c%-%C', 0, (1, maxint, '') ),
    'except_suite_finalize':     ( '%+%c%-%C', 1, (3, maxint, '') ),
    'withstmt':     ( '%|with %c:\n%+%c%-', 0, 3),
    'withasstmt':   ( '%|with %c as %c:\n%+%c%-', 0, 2, 3),
    'passstmt':		( '%|pass\n', ),
    'STORE_FAST':	( '%{pattr}', ),
    'kv':		( '%c: %c', 3, 1 ),
    'kv2':		( '%c: %c', 1, 2 ),
    'mapexpr':		( '{%[1]C}', (0, maxint, ', ') ),
    'importstmt': ( '%|import %c\n', 2),
    'importfrom': ( '%|from %[2]{pattr} import %c\n', 3 ),
    'importstar': ( '%|from %[2]{pattr} import *\n', ),
}


MAP_DIRECT = (TABLE_DIRECT, )
MAP_R0 = (TABLE_R0, -1, 0)
MAP_R = (TABLE_R, -1)

MAP = {
    'stmt':		MAP_R,
    'call_function':	MAP_R,
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
    'yield':                101,
    'yield_from':           101
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

class SourceWalkerError(Exception):
    def __init__(self, errmsg):
        self.errmsg = errmsg

    def __str__(self):
        return self.errmsg

class SourceWalker(GenericASTTraversal, object):
    stacked_params = ('f', 'indent', 'isLambda', '_globals')

    def __init__(self, version, out, scanner, showast=False,
                 debug_parser=PARSER_DEFAULT_DEBUG,
                 compile_mode='exec', is_pypy=False,
                 linestarts={}):
        GenericASTTraversal.__init__(self, ast=None)
        self.scanner = scanner
        params = {
            'f': out,
            'indent': '',
            }
        self.version = version
        self.p = get_python_parser(version, debug_parser=dict(debug_parser),
                                   compile_mode=compile_mode, is_pypy=is_pypy)
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
        self.linestarts = linestarts
        self.line_number = 0
        self.ast_errors = []

        # hide_internal suppresses displaying the additional instructions that sometimes
        # exist in code but but were not written in the source code.
        # An example is:
        # __module__ = __name__
        self.hide_internal = True
        self.name = None
        self.version = version
        self.is_pypy = is_pypy
        self.customize_for_version(is_pypy, version)

        return

    def indent_if_source_nl(self, line_number, indent):
        if (line_number != self.line_number):
            self.write("\n" + self.indent + INDENT_PER_LEVEL[:-1])
        return self.line_number

    def customize_for_version(self, is_pypy, version):
        if is_pypy:
            ########################
            # PyPy changes
            #######################
            TABLE_DIRECT.update({
                'assert_pypy':	( '%|assert %c\n' , 1 ),
                'assert2_pypy':	( '%|assert %c, %c\n' , 1, 4 ),
                'trystmt_pypy':	( '%|try:\n%+%c%-%c\n\n', 1, 2 ),
                'tryfinallystmt_pypy': ( '%|try:\n%+%c%-%|finally:\n%+%c%-\n\n', 1, 3 ),
                'assign3_pypy':     ( '%|%c, %c, %c = %c, %c, %c\n', 5, 4, 3, 0, 1, 2 ),
                'assign2_pypy':     ( '%|%c, %c = %c, %c\n', 3, 2, 0, 1),
                })
        else:
            ########################
            # Without PyPy
            #######################
            TABLE_DIRECT.update({
                'assert':		( '%|assert %c\n' , 0 ),
                'assert2':		( '%|assert %c, %c\n' , 0, 3 ),
                'trystmt':		( '%|try:\n%+%c%-%c\n\n', 1, 3 ),
                'assign2':     ( '%|%c, %c = %c, %c\n', 3, 4, 0, 1 ),
                'assign3':     ( '%|%c, %c, %c = %c, %c, %c\n', 5, 6, 7, 0, 1, 2 ),
                })
        if version < 3.0:
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
            TABLE_DIRECT.update({
                'raise_stmt2':	( '%|raise %c, %c\n', 0, 1),
            })
        else:
            # Gotta love Python for its futzing around with syntax like this
            TABLE_DIRECT.update({
                'raise_stmt2':	( '%|raise %c from %c\n', 0, 1),
            })

        if version < 2.0:
            TABLE_DIRECT.update({
                'importlist':	( '%C', (0, maxint, ', ') ),
                })
        else:
            TABLE_DIRECT.update({
                'importlist2':	( '%C', (0, maxint, ', ') ),
                })
            if version <= 2.4:
                global NAME_MODULE
                NAME_MODULE = AST('stmt',
                                  [ AST('assign',
                                        [ AST('expr',
                                              [Token('LOAD_GLOBAL', pattr='__name__',
                                                     offset=0, has_arg=True)]),
                                          AST('designator',
                                              [ Token('STORE_NAME', pattr='__module__',
                                                      offset=3, has_arg=True)])
                                        ])])
                pass
            if version <= 2.3:
                TABLE_DIRECT.update({
                    'tryfinallystmt': ( '%|try:\n%+%c%-%|finally:\n%+%c%-\n\n', 1, 4 )
                })

            elif version >= 2.5:
                ########################
                # Import style for 2.5+
                ########################
                TABLE_DIRECT.update({
                    'importmultiple': ( '%|import %c%c\n', 2, 3 ),
                    'import_cont'   : ( ', %c', 2 ),
                })

        ########################################
        # Python 2.6+
        #    except <condition> as <var>
        # vs. older:
        #    except <condition> , <var>
        #
        # For 2.6 we use the older syntax which
        # matches how we parse this in bytecode
        ########################################
        if version > 2.6:
            TABLE_DIRECT.update({
                'except_cond2':	( '%|except %c as %c:\n', 1, 5 ),
            })
        else:
            TABLE_DIRECT.update({
                'except_cond3':	 ( '%|except %c, %c:\n', 1, 6 ),
                'testtrue_then': ( 'not %p', (0, 22) ),

            })
        if 2.4 <= version <= 2.6:
            TABLE_DIRECT.update({
                'comp_for':	( ' for %c in %c', 3, 1 ),
            })
        else:
            TABLE_DIRECT.update({
                'comp_for':	( ' for %c in %c%c', 2, 0, 3 ),
            })

        if  version >= 3.0:
            TABLE_DIRECT.update({
                'funcdef_annotate': ( '\n\n%|def %c%c\n', -1, 0),
                'store_locals': ( '%|# inspect.currentframe().f_locals = __locals__\n', ),
                })

            def n_mkfunc_annotate(node):

                if self.version >= 3.3 or node[-2] == 'kwargs':
                    # LOAD_CONST code object ..
                    # LOAD_CONST        'x0'  if >= 3.3
                    # EXTENDED_ARG
                    # MAKE_FUNCTION ..
                    code = node[-4]
                elif node[-3] == 'expr':
                    code = node[-3][0]
                else:
                    # LOAD_CONST code object ..
                    # MAKE_FUNCTION ..
                    code = node[-3]

                self.indentMore()
                if self.version == 3.1:
                    annotate_last = -4
                else:
                    annotate_last = -5

                # FIXME: handle and pass full annotate args
                make_function3_annotate(self, node, isLambda=False,
                                        codeNode=code, annotate_last=annotate_last)

                if len(self.param_stack) > 1:
                    self.write('\n\n')
                else:
                    self.write('\n\n\n')
                self.indentLess()
                self.prune() # stop recursing
            self.n_mkfunc_annotate = n_mkfunc_annotate

            if version >= 3.4:
                ########################
                # Python 3.4+ Additions
                #######################
                TABLE_DIRECT.update({
                    'LOAD_CLASSDEREF':	( '%{pattr}', ),
                    })
                if version >= 3.5:
                    def n_unmapexpr(node):
                        last_n = node[0][-1]
                        for n in node[0]:
                            self.preorder(n)
                            if n != last_n:
                                self.f.write(', **')
                                pass
                            pass
                        if version >= 3.6:
                            self.f.write(')')
                        self.prune()
                        pass
                    self.n_unmapexpr = n_unmapexpr

                if version >= 3.6:
                    ########################
                    # Python 3.6+ Additions
                    #######################
                    TABLE_DIRECT.update({
                        'fstring_expr':   ( "{%c%{conversion}}", 0),
                        'fstring_single': ( "f'{%c%{conversion}}'", 0),
                        'fstring_multi':  ( "f'%c'", 0),
                        'func_args36':    ( "%c(**", 0),
                    })

                    FSTRING_CONVERSION_MAP = {1: '!s', 2: '!r', 3: '!a'}

                    def f_conversion(node):
                        node.conversion = FSTRING_CONVERSION_MAP.get(node.data[1].attr, '')

                    def n_fstring_expr(node):
                        f_conversion(node)
                        self.default(node)
                    self.n_fstring_expr = n_fstring_expr

                    def n_fstring_single(node):
                        f_conversion(node)
                        self.default(node)
                    self.n_fstring_single = n_fstring_single

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

    def set_pos_info(self, node):
        if hasattr(node, 'linestart') and node.linestart:
            self.line_number = node.linestart

    def preorder(self, node=None):
        super(SourceWalker, self).preorder(node)
        self.set_pos_info(node)

    def indentMore(self, indent=TAB):
        self.indent += indent

    def indentLess(self, indent=TAB):
        self.indent = self.indent[:-len(indent)]

    def traverse(self, node, indent=None, isLambda=False):
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

    def is_return_none(self, node):
        # Is there a better way?
        ret = (node[0] == 'ret_expr'
               and node[0][0] == 'expr'
               and node[0][0][0] == 'LOAD_CONST'
               and node[0][0][0].pattr is None)
        if self.version <= 2.6:
            return ret
        else:
            # FIXME: should the AST expression be folded into
            # the global RETURN_NONE constant?
            return (ret or
                    node == AST('return_stmt',
                                [AST('ret_expr', [NONE]), Token('RETURN_VALUE')]))

    def n_return_stmt(self, node):
        if self.params['isLambda']:
            self.preorder(node[0])
            self.prune()
        else:
            self.write(self.indent, 'return')
            # One reason we worry over whether we use "return None" or "return"
            # is that inside a generator, "return None" is illegal.
            # Thank you, Python!
            if (self.return_none or not self.is_return_none(node)):
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
            if self.return_none or not self.is_return_none(node):
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
        if 3.3 <= self.version <= 3.4:
            self.preorder(node[0][0][0][0])
        elif self.version >= 3.5:
            self.preorder(node[0])
        else:
            assert False, "dunno about this python version"
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

    def n_str(self, node):
        self.write(node[0].pattr)
        self.prune()

    def pp_tuple(self, tup):
        """Pretty print a tuple"""
        last_line = self.f.getvalue().split("\n")[-1]
        l = len(last_line)+1
        indent = ' ' * l
        self.write('(')
        sep = ''
        for item in tup:
            self.write(sep)
            l += len(sep)
            s = repr(item)
            l += len(s)
            self.write(s)
            sep = ','
            if l > LINE_LENGTH:
                l = 0
                sep += '\n' + indent
            else:
                sep += ' '
                pass
            pass
        if len(tup) == 1:
            self.write(", ")
        self.write(')')

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
        elif isinstance(data, tuple):
            self.pp_tuple(data)
        else:
            self.write(repr(data))
        # LOAD_CONST is a terminal, so stop processing/recursing early
        self.prune()

    def n_delete_subscr(self, node):
        if node[-2][0] == 'build_list' and node[-2][0][-1].type.startswith('BUILD_TUPLE'):
            if node[-2][0][-1] != 'BUILD_TUPLE_0':
                node[-2][0].type = 'build_tuple2'
        self.default(node)

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

    def n_ifelsestmt(self, node, preprocess=False):
        else_suite = node[3]

        n = else_suite[0]

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
            self.n_ifelsestmt(n, preprocess=True)
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
        store_node = node[-1][-1]
        assert store_node.type.startswith('STORE_')
        iname = node[0].pattr  # import name
        sname = store_node.pattr # store_name
        if iname and iname == sname or iname.startswith(sname + '.'):
            self.write(iname)
        else:
            self.write(iname, ' as ', sname)
        self.prune() # stop recursing

    n_import_as_cont = n_import_as

    def n_importfrom(self, node):
        relative_path_index = 0
        if self.version >= 2.5 and node[relative_path_index].pattr > 0:
            node[2].pattr = '.'*node[relative_path_index].pattr + node[2].pattr
        self.default(node)

    n_importstar = n_importfrom

    def n_mkfunc(self, node):

        if self.version >= 3.3 or node[-2] == 'kwargs':
            # LOAD_CONST code object ..
            # LOAD_CONST        'x0'  if >= 3.3
            # MAKE_FUNCTION ..
            code = node[-3]
        elif node[-2] == 'expr':
            code = node[-2][0]
        else:
            # LOAD_CONST code object ..
            # MAKE_FUNCTION ..
            code = node[-2]

        func_name = code.attr.co_name
        self.write(func_name)

        self.indentMore()
        self.make_function(node, isLambda=False, codeNode=code)

        if len(self.param_stack) > 1:
            self.write('\n\n')
        else:
            self.write('\n\n\n')
        self.indentLess()
        self.prune() # stop recursing

    def make_function(self, node, isLambda, nested=1,
                      codeNode=None, annotate=None):
        if self.version >= 3.0:
            make_function3(self, node, isLambda, nested, codeNode)
        else:
            make_function2(self, node, isLambda, nested, codeNode)

    def n_mklambda(self, node):
        self.make_function(node, isLambda=True, codeNode=node[-2])
        self.prune() # stop recursing

    def n_list_compr(self, node):
        """List comprehensions the way they are done in Python 2.
        """
        p = self.prec
        self.prec = 27
        if self.version >= 2.7:
            if self.is_pypy:
                self.n_list_compr_pypy27(node)
                return
            n = node[-1]
        elif node[-1] == 'del_stmt':
            if node[-2] == 'JUMP_BACK':
                n = node[-3]
            else:
                n = node[-2]

        assert n == 'list_iter'

        # find innermost node
        while n == 'list_iter':
            n = n[0] # recurse one step
            if   n == 'list_for':	n = n[3]
            elif n == 'list_if':	n = n[2]
            elif n == 'list_if_not': n= n[2]
        assert n == 'lc_body'
        self.write( '[ ')

        if self.version >= 2.7:
            expr = n[0]
            list_iter = node[-1]
        else:
            expr = n[1]
            if node[-2] == 'JUMP_BACK':
                list_iter = node[-3]
            else:
                list_iter = node[-2]

        assert expr == 'expr'
        assert list_iter == 'list_iter'

        # FIXME: use source line numbers for directing line breaks

        line_number = self.line_number
        last_line = self.f.getvalue().split("\n")[-1]
        l = len(last_line)
        indent = ' ' * (l-1)

        self.preorder(expr)
        line_number = self.indent_if_source_nl(line_number, indent)
        self.preorder(list_iter)
        l2 = self.indent_if_source_nl(line_number, indent)
        if l2 != line_number:
            self.write(' ' * (len(indent) - len(self.indent) - 1) + ']')
        else:
            self.write( ' ]')
        self.prec = p
        self.prune() # stop recursing

    def n_list_compr_pypy27(self, node):
        """List comprehensions the way they are done in PYPY Python 2.7.
        """
        p = self.prec
        self.prec = 27
        if node[-1].type == 'list_iter':
            n = node[-1]
        elif self.is_pypy and node[-1] == 'JUMP_BACK':
            n = node[-2]
        list_expr = node[1]

        if len(node) >= 3:
            designator = node[3]
        elif self.is_pypy and n[0] == 'list_for':
            designator = n[0][2]

        assert n == 'list_iter'
        assert designator == 'designator'

        # find innermost node
        while n == 'list_iter':
            n = n[0] # recurse one step
            if   n == 'list_for':	n = n[3]
            elif n == 'list_if':	n = n[2]
            elif n == 'list_if_not': n= n[2]
        assert n == 'lc_body'
        self.write( '[ ')

        expr = n[0]
        if self.is_pypy and node[-1] == 'JUMP_BACK':
            list_iter = node[-2]
        else:
            list_iter = node[-1]

        assert expr == 'expr'
        assert list_iter == 'list_iter'

        # FIXME: use source line numbers for directing line breaks

        self.preorder(expr)
        self.preorder(list_expr)
        self.write( ' ]')
        self.prec = p
        self.prune() # stop recursing

    def comprehension_walk(self, node, iter_index, code_index=-5):
        p = self.prec
        self.prec = 27

        # FIXME: clean this up
        if self.version > 3.0 and node == 'dictcomp':
            cn = node[1]
        elif self.version < 2.7 and node == 'genexpr':
            if node[0] == 'LOAD_GENEXPR':
                cn = node[0]
            elif node[0] == 'load_closure':
                cn = node[1]

        elif self.version > 3.0 and node == 'genexpr':
            if node[0] == 'load_genexpr':
                load_genexpr = node[0]
            elif node[1] == 'load_genexpr':
                load_genexpr = node[1]
            cn = load_genexpr[0]
        elif hasattr(node[code_index], 'attr'):
            # Python 2.5+ (and earlier?) does this
            cn = node[code_index]
        else:
            if len(node[1]) > 1 and hasattr(node[1][1], 'attr'):
                # Python 3.3+ does this
                cn = node[1][1]
            elif hasattr(node[1][0], 'attr'):
                # Python 3.2 does this
                cn = node[1][0]
            else:
                assert False, "Can't find code for comprehension"

        assert iscode(cn.attr)

        code = Code(cn.attr, self.scanner, self.currentclass)
        ast = self.build_ast(code._tokens, code._customize)
        self.customize(code._customize)
        ast = ast[0][0][0]

        n = ast[iter_index]
        assert n == 'comp_iter', n

        # find innermost node
        while n == 'comp_iter': # list_iter
            n = n[0] # recurse one step
            if n == 'comp_for':
                if n[0] == 'SETUP_LOOP':
                    n = n[4]
                else:
                    n = n[3]
            elif n == 'comp_if':
                n = n[2]
            elif n == 'comp_ifnot':
                n = n[2]

        assert n == 'comp_body', n

        self.preorder(n[0])
        self.write(' for ')
        self.preorder(ast[iter_index-1])
        self.write(' in ')
        if node[2] == 'expr':
            iter_expr = node[2]
        else:
            iter_expr = node[-3]
        assert iter_expr == 'expr'
        self.preorder(iter_expr)
        self.preorder(ast[iter_index])
        self.prec = p

    def n_genexpr(self, node):
        self.write('(')
        if self.version > 3.2:
            code_index = -6
        else:
            code_index = -5
        self.comprehension_walk(node, iter_index=3, code_index=code_index)
        self.write(')')
        self.prune()

    def n_setcomp(self, node):
        self.write('{')
        if node[0] in ['LOAD_SETCOMP', 'LOAD_DICTCOMP']:
            self.comprehension_walk3(node, 1, 0)
        elif node[0].type == 'load_closure' and self.version >= 3.0:
            self.setcomprehension_walk3(node, collection_index=4)
        else:
            self.comprehension_walk(node, iter_index=4)
        self.write('}')
        self.prune()

    def comprehension_walk3(self, node, iter_index, code_index=-5):
        """
        List comprehensions the way they are done in Python3.
        They're more other comprehensions, e.g. set comprehensions
        See if we can combine code.
        """
        p = self.prec
        self.prec = 27
        code = node[code_index].attr

        assert iscode(code), node[code_index]
        code = Code(code, self.scanner, self.currentclass)

        ast = self.build_ast(code._tokens, code._customize)
        self.customize(code._customize)
        # skip over stmts sstmt smt
        ast = ast[0][0][0]
        designator = None
        if ast in ['setcomp_func', 'dictcomp_func']:
            for k in ast:
                if k == 'comp_iter':
                    n = k
                elif k == 'designator':
                    designator = k
                    pass
                pass
            pass
        else:
            ast = ast[0][0]
            n = ast[iter_index]
            assert n == 'list_iter', n

        # FIXME: I'm not totally sure this is right.

        # find innermost node
        if_node = None
        comp_for = None
        comp_designator = None
        if n == 'comp_iter':
            comp_for = n
            comp_designator = ast[3]

        have_not = False
        while n in ('list_iter', 'comp_iter'):
            n = n[0] # recurse one step
            if n in ('list_for', 'comp_for'):
                if n[2] == 'designator':
                    designator = n[2]
                n = n[3]
            elif n in ('list_if', 'list_if_not', 'comp_if', 'comp_ifnot'):
                have_not = n in ('list_if_not', 'comp_ifnot')
                if_node = n[0]
                if n[1] == 'designator':
                    designator = n[1]
                n = n[2]
                pass
            pass

        # Python 2.7+ starts including set_comp_body
        # Python 3.5+ starts including setcomp_func
        assert n.type in ('lc_body', 'comp_body', 'setcomp_func', 'set_comp_body'), ast
        assert designator, "Couldn't find designator in list/set comprehension"

        self.preorder(n[0])
        self.write(' for ')
        if comp_designator:
            self.preorder(comp_designator)
        else:
            self.preorder(designator)

        self.write(' in ')
        self.preorder(node[-3])
        if comp_designator:
            self.preorder(comp_for)
        elif if_node:
            self.write(' if ')
            if have_not:
                self.write('not ')
            self.preorder(if_node)
        self.prec = p

    def listcomprehension_walk2(self, node):
        """List comprehensions the way they are done in Python 2.
        They're more other comprehensions, e.g. set comprehensions
        See if we can combine code.
        """
        p = self.prec
        self.prec = 27

        code = Code(node[1].attr, self.scanner, self.currentclass)
        ast = self.build_ast(code._tokens, code._customize)
        self.customize(code._customize)
        if node == 'setcomp':
            ast = ast[0][0][0]
        else:
            ast = ast[0][0][0][0][0]

        n = ast[1]
        collection = node[-3]
        list_if = None
        assert n == 'list_iter'

        # find innermost node
        while n == 'list_iter':
            n = n[0] # recurse one step
            if n == 'list_for':
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
            self.comprehension_walk3(node, 1, 0)
        self.write(']')
        self.prune()

    n_dictcomp = n_setcomp

    def setcomprehension_walk3(self, node, collection_index):
        """List comprehensions the way they are done in Python3.
        They're more other comprehensions, e.g. set comprehensions
        See if we can combine code.
        """
        p = self.prec
        self.prec = 27

        code = Code(node[1].attr, self.scanner, self.currentclass)
        ast = self.build_ast(code._tokens, code._customize)
        self.customize(code._customize)
        ast = ast[0][0][0]
        designator = ast[3]
        collection = node[collection_index]

        n = ast[4]
        list_if = None
        assert n == 'comp_iter'

        # find innermost node
        while n == 'comp_iter':
            n = n[0] # recurse one step
            # FIXME: adjust for set comprehension
            if n == 'list_for':
                designator = n[2]
                n = n[3]
            elif n in ('list_if', 'list_if_not', 'comp_if', 'comp_if_not'):
                # FIXME: just a guess
                if n[0].type == 'expr':
                    list_if = n
                else:
                    list_if = n[1]
                n = n[2]
                pass
            pass

        assert n == 'comp_body', ast

        self.preorder(n[0])
        self.write(' for ')
        self.preorder(designator)
        self.write(' in ')
        self.preorder(collection)
        if list_if:
            self.preorder(list_if)
        self.prec = p

    def n_classdef(self, node):
        # class definition ('class X(A,B,C):')
        cclass = self.currentclass

        if self.version > 3.0:
            if node == 'classdefdeco2':
                currentclass = node[1][2].pattr
                buildclass = node
            else:
                currentclass = node[1][0].pattr
                buildclass = node[0]

            assert 'mkfunc' == buildclass[1]
            mkfunc = buildclass[1]
            if mkfunc[0] == 'kwargs':
                if 3.0 <= self.version <= 3.2:
                    for n in mkfunc:
                        if hasattr(n, 'attr') and iscode(n.attr):
                            subclass = n.attr
                            break
                        elif n == 'expr':
                            subclass = n[0].attr
                        pass
                    pass
                else:
                    for n in mkfunc:
                        if hasattr(n, 'attr') and iscode(n.attr):
                            subclass = n.attr
                            break
                        pass
                    pass
                if node == 'classdefdeco2':
                    subclass_info = node
                else:
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
            if node == 'classdefdeco2':
                buildclass = node
            else:
                buildclass = node[0]
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

        n_subclasses = len(node[:-1])
        if n_subclasses > 0 or self.version > 2.1:
            # Not an old-style pre-2.2 class
            self.write('(')

        line_separator = ', '
        sep = ''
        for elem in node[:-1]:
            value = self.traverse(elem)
            self.write(sep, value)
            sep = line_separator

        if n_subclasses > 0 or self.version > 2.1:
            # Not an old-style pre-2.2 class
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
        'mapexpr' is something like k = {'a': 1, 'b': 42}"
        We will source-code use line breaks to guide us when to break.
        """
        p = self.prec
        self.prec = 100

        self.indentMore(INDENT_PER_LEVEL)
        sep = INDENT_PER_LEVEL[:-1]
        self.write('{')
        line_number = self.line_number

        if self.version >= 3.0 and not self.is_pypy:
            if node[0].type.startswith('kvlist'):
                # Python 3.5+ style key/value list in mapexpr
                kv_node = node[0]
                l = list(kv_node)
                i = 0
                # Respect line breaks from source
                while i < len(l):
                    self.write(sep)
                    name = self.traverse(l[i], indent='')
                    if i > 0:
                        line_number = self.indent_if_source_nl(line_number,
                                                               self.indent + INDENT_PER_LEVEL[:-1])
                    line_number = self.line_number
                    self.write(name, ': ')
                    value = self.traverse(l[i+1], indent=self.indent+(len(name)+2)*' ')
                    self.write(value)
                    sep = ","
                    if line_number != self.line_number:
                        sep += "\n" + self.indent + INDENT_PER_LEVEL[:-1]
                        line_number = self.line_number
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
                    self.write(sep)
                    name = self.traverse(l[i+1], indent='')
                    if i > 0:
                        line_number = self.indent_if_source_nl(line_number,
                                                               self.indent + INDENT_PER_LEVEL[:-1])
                        pass
                    line_number = self.line_number
                    self.write(name, ': ')
                    value = self.traverse(l[i], indent=self.indent+(len(name)+2)*' ')
                    self.write(value)
                    sep = ","
                    if line_number != self.line_number:
                        sep += "\n" + self.indent + INDENT_PER_LEVEL[:-1]
                        line_number = self.line_number
                    else:
                        sep += " "
                    i += 3
                    pass
                pass
            pass
        else:
            # Python 2 style kvlist
            assert node[-1].type.startswith('kvlist')
            kv_node = node[-1] # goto kvlist

            first_time = True
            for kv in kv_node:
                assert kv in ('kv', 'kv2', 'kv3')
                # kv ::= DUP_TOP expr ROT_TWO expr STORE_SUBSCR
                # kv2 ::= DUP_TOP expr expr ROT_THREE STORE_SUBSCR
                # kv3 ::= expr expr STORE_MAP

                # FIXME: DRY this and the above
                indent = self.indent + "  "
                if kv == 'kv':
                    self.write(sep)
                    name = self.traverse(kv[-2], indent='')
                    if first_time:
                        line_number = self.indent_if_source_nl(line_number, indent)
                        first_time = False
                        pass
                    line_number = self.line_number
                    self.write(name, ': ')
                    value = self.traverse(kv[1], indent=self.indent+(len(name)+2)*' ')
                elif kv == 'kv2':
                    self.write(sep)
                    name = self.traverse(kv[1], indent='')
                    if first_time:
                        line_number = self.indent_if_source_nl(line_number, indent)
                        first_time = False
                        pass
                    line_number = self.line_number
                    self.write(name, ': ')
                    value = self.traverse(kv[-3], indent=self.indent+(len(name)+2)*' ')
                elif kv == 'kv3':
                    self.write(sep)
                    name = self.traverse(kv[-2], indent='')
                    if first_time:
                        line_number = self.indent_if_source_nl(line_number, indent)
                        first_time = False
                        pass
                    line_number = self.line_number
                    self.write(name, ': ')
                    line_number = self.line_number
                    value = self.traverse(kv[0], indent=self.indent+(len(name)+2)*' ')
                    pass
                self.write(value)
                sep = ","
                if line_number != self.line_number:
                    sep += "\n" + self.indent + "  "
                    line_number = self.line_number
        if sep.startswith(",\n"):
            self.write(sep[1:])
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
        have_star = False
        if lastnodetype.startswith('BUILD_LIST'):
            # 3.5+ has BUILD_LIST_UNPACK
            if lastnodetype == 'BUILD_LIST_UNPACK':
                # FIXME: need to handle range of BUILD_LIST_UNPACK
                have_star = True
                endchar = ''
            else:
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
        sep = ''

        for elem in flat_elems:
            if elem == 'ROT_THREE':
                continue
            assert elem == 'expr'
            line_number = self.line_number
            value = self.traverse(elem)
            if line_number != self.line_number:
                sep += '\n' + self.indent + INDENT_PER_LEVEL[:-1]
            else:
                if sep != '': sep += ' '
            if have_star:
                sep += '*'
            self.write(sep, value)
            sep = ','
        if lastnode.attr == 1 and lastnodetype.startswith('BUILD_TUPLE'):
            self.write(',')
        self.write(endchar)
        self.indentLess(INDENT_PER_LEVEL)
        self.prec = p
        self.prune()

    def n_unpack(self, node):
        if node[0].type.startswith('UNPACK_EX'):
            # Python 3+
            before_count, after_count = node[0].attr
            for i in range(before_count+1):
                self.preorder(node[i])
                if i != 0:
                    self.write(', ')
            self.write('*')
            for i in range(1, after_count+2):
                self.preorder(node[before_count+i])
                if i != after_count + 1:
                    self.write(', ')
            self.prune()
            return
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
        if node[-2][0] == 'unpack':
            node[-2][0].type = 'unpack_w_parens'
        self.default(node)

    def engine(self, entry, startnode):
        """The format template interpetation engine.  See the comment at the
        beginning of this module for the how we interpret format specifications such as
        %c, %C, and so on.
        """

        # self.println("----> ", startnode.type)
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
            elif typ == '+':
                self.line_number += 1
                self.indentMore()
            elif typ == '-':
                self.line_number += 1
                self.indentLess()
            elif typ == '|':
                self.line_number += 1
                self.write(self.indent)
            # Used mostly on the LHS of an assignment
            # BUILD_TUPLE_n is pretty printed and may take care of other uses.
            elif typ == ',':
                if (node.type in ('unpack', 'unpack_w_parens') and
                    node[0].attr == 1):
                    self.write(',')
            elif typ == 'c':
                if isinstance(entry[arg], int):
                    entry_node = node[entry[arg]]
                    self.preorder(entry_node)
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
            elif typ == 'x':
                # This code is only used in fragments
                assert isinstance(entry[arg], tuple)
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
        mapping = self._get_mapping(node)
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
        Special handling for opcodes, such as those that take a variable number
        of arguments -- we add a new entry for each in TABLE_R.
        """
        for k, v in list(customize.items()):
            if k in TABLE_R:
                continue
            op = k[ :k.rfind('_') ]

            if k.startswith('CALL_METHOD'):
                # This happens in PyPy only
                TABLE_R[k] = ('%c(%P)', 0, (1, -1, ', ', 100))
            elif op == 'CALL_FUNCTION':
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

        first_stmt = ast[0][0]
        if 3.0 <= self.version <= 3.3:
            try:
                if first_stmt[0] == 'store_locals':
                    if self.hide_internal:
                        del ast[0]
                        first_stmt = ast[0][0]
            except:
                pass

        try:
            if first_stmt == NAME_MODULE:
                if self.hide_internal:
                    del ast[0]
                    first_stmt = ast[0][0]
            pass
        except:
            pass

        have_qualname = False
        if self.version < 3.0:
            # Should we ditch this in favor of the "else" case?
            qualname = '.'.join(self.classes)
            QUAL_NAME = AST('stmt',
                            [ AST('assign',
                                  [ AST('expr', [Token('LOAD_CONST', pattr=qualname)]),
                                    AST('designator', [ Token('STORE_NAME', pattr='__qualname__')])
                                  ])])
            have_qualname = (ast[0][0] == QUAL_NAME)
        else:
            # Python 3.4+ has constants like 'cmp_to_key.<locals>.K'
            # which are not simple classes like the < 3 case.
            try:
                if (first_stmt[0] == 'assign' and
                    first_stmt[0][0][0] == 'LOAD_CONST' and
                    first_stmt[0][1] == 'designator' and
                    first_stmt[0][1][0] == Token('STORE_NAME', pattr='__qualname__')):
                    have_qualname = True
            except:
                pass

        if have_qualname:
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
                if print_docstring(self, indent, docstring):
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

        old_name = self.name
        self.gen_source(ast, code.co_name, code._customize)
        self.name = old_name
        code._tokens = None; code._customize = None # save memory
        self.classes.pop(-1)

    def gen_source(self, ast, name, customize, isLambda=False, returnNone=False):
        """convert AST to Python source code"""

        rn = self.return_none
        self.return_none = returnNone
        old_name = self.name
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
        self.name = old_name
        self.return_none = rn

    def build_ast(self, tokens, customize, isLambda=False,
                  noneInNames=False, isTopLevel=False):

        # assert isinstance(tokens[0], Token)

        if isLambda:
            tokens.append(Token('LAMBDA_MARKER'))
            try:
                ast = python_parser.parse(self.p, tokens, customize)
            except python_parser.ParserError, e:
                raise ParserError(e, tokens)
            except AssertionError, e:
                raise ParserError(e, tokens)
            maybe_show_ast(self.showast, ast)
            return ast

        # The bytecode for the end of the main routine has a
        # "return None". However you can't issue a "return" statement in
        # main. So as the old cigarette slogan goes: I'd rather switch (the token stream)
        # than fight (with the grammar to not emit "return None").
        if self.hide_internal:
            if len(tokens) >= 2 and not noneInNames:
                if tokens[-1].type == 'RETURN_VALUE':
                    # Python 3.4's classes can add a "return None" which is
                    # invalid syntax.
                    if tokens[-2].type == 'LOAD_CONST':
                        if isTopLevel or tokens[-2].pattr is None:
                            del tokens[-2:]
                        else:
                            tokens.append(Token('RETURN_LAST'))
                    else:
                        tokens.append(Token('RETURN_LAST'))
            if len(tokens) == 0:
                return PASS

        # Build AST from disassembly.
        try:
            ast = python_parser.parse(self.p, tokens, customize)
        except python_parser.ParserError, e:
            raise ParserError(e, tokens)
        except AssertionError, e:
            raise ParserError(e, tokens)

        maybe_show_ast(self.showast, ast)

        checker(ast, False, self.ast_errors)

        return ast

    @classmethod
    def _get_mapping(cls, node):
        return MAP.get(node, MAP_DIRECT)


def deparse_code(version, co, out=sys.stdout, showasm=None, showast=False,
                 showgrammar=False, code_objects={}, compile_mode='exec', is_pypy=False):
    """
    ingests and deparses a given code block 'co'
    """

    assert iscode(co)
    # store final output stream for case of error
    scanner = get_scanner(version, is_pypy=is_pypy)

    tokens, customize = scanner.ingest(co, code_objects=code_objects, show_asm=showasm)

    debug_parser = dict(PARSER_DEFAULT_DEBUG)
    if showgrammar:
        debug_parser['reduce'] = showgrammar
        debug_parser['errorstack'] = True

    #  Build AST from disassembly.
    linestarts = dict(scanner.opc.findlinestarts(co))
    deparsed = SourceWalker(version, out, scanner, showast=showast,
                            debug_parser=debug_parser, compile_mode=compile_mode,
                            is_pypy=is_pypy,
                            linestarts=linestarts)

    isTopLevel = co.co_name == '<module>'
    deparsed.ast = deparsed.build_ast(tokens, customize, isTopLevel=isTopLevel)

    assert deparsed.ast == 'stmts', 'Should have parsed grammar start'

    del tokens # save memory

    deparsed.mod_globs = find_globals(deparsed.ast, set())

    # convert leading '__doc__ = "..." into doc string
    try:
        if deparsed.ast[0][0] == ASSIGN_DOC_STRING(co.co_consts[0]):
            print_docstring(deparsed, '', co.co_consts[0])
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

    if deparsed.ast_errors:
        deparsed.write("# NOTE: have internal decompilation grammar errors.\n")
        deparsed.write("# Use -t option to show full context.")
        for err in deparsed.ast_errors:
            deparsed.write(err)
        raise SourceWalkerError("Deparsing hit an internal grammar-rule bug")

    if deparsed.ERROR:
        raise SourceWalkerError("Deparsing stopped due to parse error")
    return deparsed

if __name__ == '__main__':
    def deparse_test(co):
        "This is a docstring"
        sys_version = float(sys.version[0:3])
        deparsed = deparse_code(sys_version, co, showasm='after', showast=True)
        # deparsed = deparse_code(sys_version, co, showasm=None, showast=False,
        #                         showgrammar=True)
        print(deparsed.text)
        return
    deparse_test(deparse_test.func_code)
