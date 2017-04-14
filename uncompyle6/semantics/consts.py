#  Copyright (c) 2017 by Rocky Bernstein
"""Constants used in pysource.py"""

import re, sys
from uncompyle6.parsers.astnode import AST
from uncompyle6 import PYTHON3
from uncompyle6.scanners.tok import Token, NoneToken

if PYTHON3:
    minint = -sys.maxsize-1
    maxint = sys.maxsize
else:
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
    'BINARY_TRUE_DIVIDE':	( '/' ,),   # Not in <= 2.1
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
    'INPLACE_TRUE_DIVIDE':	( '/=' ,),  # Not in <= 2.1; 2.6 generates INPLACE_DIVIDE only?
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
    'conditionalTrue':  ( '%p if 1 else %p', (0, 27), (2, 27)),
    'ret_cond':     ( '%p if %p else %p', (2, 27), (0, 27), (-1, 27)),
    'conditionalnot':  ( '%p if not %p else %p', (2, 27), (0, 22), (4, 27)),
    'ret_cond_not':  ( '%p if not %p else %p', (2, 27), (0, 22), (-1, 27)),
    'conditional_lambda':  ( '(%c if %c else %c)', 2, 0, 3),
    'return_lambda':    ('%c', 0),
    'compare':		( '%p %[-1]{pattr} %p', (0, 19), (1, 19) ),
    'cmp_list':		( '%p %p', (0, 29), (1, 30)),
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
    'ifelsestmtr2':	( '%|if %c:\n%+%c%-%|else:\n%+%c%-\n\n', 0, 1, 3 ), # has COME_FROM
    'elifelsestmtr':	( '%|elif %c:\n%+%c%-%|else:\n%+%c%-\n\n', 0, 1, 2 ),
    'elifelsestmtr2':	( '%|elif %c:\n%+%c%-%|else:\n%+%c%-\n\n', 0, 1, 3 ), # has COME_FROM

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

# Operator precidence
# See https://docs.python.org/3/reference/expressions.html
# or https://docs.python.org/3/reference/expressions.html
# for a list.
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
