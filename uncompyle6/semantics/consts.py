#  Copyright (c) 2017-2019 by Rocky Bernstein
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
"""Constants and initial table values used in pysource.py and fragments.py"""

import re, sys
from uncompyle6.parsers.treenode import SyntaxTree
from uncompyle6 import PYTHON3
from uncompyle6.scanners.tok import Token, NoneToken

if PYTHON3:
    minint = -sys.maxsize-1
    maxint = sys.maxsize
else:
    minint = -sys.maxint-1
    maxint = sys.maxint


# Operator precidence See
# https://docs.python.org/2/reference/expressions.html#operator-precedence
# or
# https://docs.python.org/3/reference/expressions.html#operator-precedence
# for a list. We keep the same top-to-botom order here as in the above links,
# so we start with low precedence (high values) and go down in value.

# Things at the bottom of this list below with high precedence (low value) will
# tend to have parenthesis around them. Things at the top
# of the list will tend not to have parenthesis around them.

# Note: The values in this table are even numbers. Inside
# various templates we use odd values. Avoiding equal-precedent comparisons
# avoids ambiguity what to do when the precedence is equal.

# The precidence of a key below applies the key, a node, and the its
# *parent*. A node however sometimes sets the precidence for its
# children. For example, "call" has precidence 2 so we don't get
# additional the additional parenthesis of: ".. op (call())".  However
# for call's children, it parameters, we set the the precidence high,
# say to 100, to make sure we avoid additional prenthesis in
# call((.. op ..)).

PRECEDENCE = {
    'yield':                 102,
    'yield_from':            102,

    '_mklambda':              30,

    'conditional':            28, # Conditional expression
    'conditional_lamdba':     28, # Lambda expression
    'conditional_not_lamdba': 28, # Lambda expression
    'conditionalnot':         28,
    'if_expr_true':           28,
    'ret_cond':               28,

    'or':                     26, # Boolean OR
    'ret_or':                 26,

    'and':                    24, # Boolean AND
    'compare':                20, # in, not in, is, is not, <, <=, >, >=, !=, ==
    'ret_and':                24,
    'unary_not':              22, # Boolean NOT

    'BINARY_AND':             14, # Bitwise AND
    'BINARY_OR':              18, # Bitwise OR
    'BINARY_XOR':             16, # Bitwise XOR

    'BINARY_LSHIFT':          12, # Shifts <<
    'BINARY_RSHIFT':          12, # Shifts >>

    'BINARY_ADD':             10, # -
    'BINARY_SUBTRACT':        10, # +

    'BINARY_DIVIDE':          8,  # /
    'BINARY_FLOOR_DIVIDE':    8,  # //
    'BINARY_MATRIX_MULTIPLY': 8,  # @
    'BINARY_MODULO':          8,  # Remainder, %
    'BINARY_MULTIPLY':        8,  # *
    'BINARY_TRUE_DIVIDE':     8,  # Division /

    'unary_op':               6,  # +x, -x, ~x

    'BINARY_POWER':           4,  # Exponentiation, *

    'attribute':              2,  # x.attribute
    'buildslice2':            2,  # x[index]
    'buildslice3':            2,  # x[index:index]
    'call':                   2,  # x(arguments...)
    'delete_subscript':       2,
    'slice0':                 2,
    'slice1':                 2,
    'slice2':                 2,
    'slice3':                 2,
    'store_subscript':        2,
    'subscript':              2,
    'subscript2':             2,

    'dict':                   0,  # {expressions...}
    'dict_comp':              0,
    'generator_exp':          0,  # (expressions...)
    'list':                   0,  # [expressions...]
    'list_comp':              0,
    'set_comp':               0,
    'set_comp_expr':          0,
    'unary_convert':          0,
}

LINE_LENGTH = 80

# Some parse trees created below are used for comparing code
# fragments (like 'return None' at the end of functions).

RETURN_LOCALS = SyntaxTree('return',
                    [ SyntaxTree('ret_expr', [SyntaxTree('expr', [ Token('LOAD_LOCALS') ])]),
                      Token('RETURN_VALUE')])

NONE = SyntaxTree('expr', [ NoneToken ] )

RETURN_NONE = SyntaxTree('stmt',
                  [ SyntaxTree('return',
                        [ NONE, Token('RETURN_VALUE')]) ])

PASS = SyntaxTree('stmts',
           [ SyntaxTree('sstmt',
                 [ SyntaxTree('stmt',
                       [ SyntaxTree('pass', [])])])])

ASSIGN_DOC_STRING = lambda doc_string, doc_load: \
  SyntaxTree('stmt',
      [ SyntaxTree('assign',
            [ SyntaxTree('expr', [ Token(doc_load, pattr=doc_string, attr=doc_string) ]),
              SyntaxTree('store', [ Token('STORE_NAME', pattr='__doc__')])
            ])])

NAME_MODULE = SyntaxTree('stmt',
                [ SyntaxTree('assign',
                    [ SyntaxTree('expr',
                          [Token('LOAD_NAME', pattr='__name__', offset=0, has_arg=True)]),
                      SyntaxTree('store',
                          [ Token('STORE_NAME', pattr='__module__', offset=3, has_arg=True)])
                      ])])

# God intended \t, but Python has decided to use 4 spaces.
# If you want real tabs, use Go.
# TAB = '\t'
TAB = ' ' * 4
INDENT_PER_LEVEL = ' ' # additional intent per pretty-print level

TABLE_R = {
    'STORE_ATTR':	( '%c.%[1]{pattr}', 0),
    'DELETE_ATTR':	( '%|del %c.%[-1]{pattr}\n', 0 ),
}

TABLE_R0 = {
#    'BUILD_LIST':	( '[%C]',      (0,-1,', ') ),
#    'BUILD_TUPLE':	( '(%C)',      (0,-1,', ') ),
#    'CALL_FUNCTION':	( '%c(%P)', 0, (1,-1,', ') ),
}

TABLE_DIRECT = {
    'BINARY_ADD':               ( '+' ,),
    'BINARY_SUBTRACT':          ( '-' ,),
    'BINARY_MULTIPLY':          ( '*' ,),
    'BINARY_DIVIDE':            ( '/' ,),
    'BINARY_MATRIX_MULTIPLY':   ( '@' ,),
    'BINARY_TRUE_DIVIDE':       ( '/' ,),   # Not in <= 2.1
    'BINARY_FLOOR_DIVIDE':      ( '//' ,),
    'BINARY_MODULO':            ( '%%',),
    'BINARY_POWER':             ( '**',),
    'BINARY_LSHIFT':            ( '<<',),
    'BINARY_RSHIFT':            ( '>>',),
    'BINARY_AND':               ( '&' ,),
    'BINARY_OR':                ( '|' ,),
    'BINARY_XOR':               ( '^' ,),
    'INPLACE_ADD':              ( '+=' ,),
    'INPLACE_SUBTRACT':         ( '-=' ,),
    'INPLACE_MULTIPLY':         ( '*=' ,),
    'INPLACE_MATRIX_MULTIPLY':  ( '@=' ,),
    'INPLACE_DIVIDE':           ( '/=' ,),
    'INPLACE_TRUE_DIVIDE':  ( '/=' ,),  # Not in <= 2.1; 2.6 generates INPLACE_DIVIDE only?
    'INPLACE_FLOOR_DIVIDE':     ( '//=' ,),
    'INPLACE_MODULO':           ( '%%=',),
    'INPLACE_POWER':            ( '**=',),
    'INPLACE_LSHIFT':           ( '<<=',),
    'INPLACE_RSHIFT':           ( '>>=',),
    'INPLACE_AND':              ( '&=' ,),
    'INPLACE_OR':               ( '|=' ,),
    'INPLACE_XOR':              ( '^=' ,),

    # bin_op (formerly "binary_expr") is the Python AST BinOp
    'bin_op':                  ( '%c %c %c', 0,
                                (-1, 'binary_operator'),
                                ( 1, 'expr' ) ),

    'UNARY_POSITIVE':           ( '+',),
    'UNARY_NEGATIVE':           ( '-',),
    'UNARY_INVERT':             ( '~'),

    # unary_op (formerly "unary_expr") is the Python AST UnaryOp
    'unary_op':                 ( '%c%c',
                                 (1, 'unary_operator'),
                                 (0, 'expr') ),

    'unary_not':	            ( 'not %c',
                                  (0, 'expr' ) ),
    'unary_convert':            ( '`%c`',
                                  (0, 'expr' ), ),
    'get_iter':	                ( 'iter(%c)',
                                  (0, 'expr'), ),
    'slice0':		        ( '%c[:]',
                                  (0, 'expr'), ),
    'slice1':		        ( '%c[%p:]',
                                  (0, 'expr'),
                                  (1, 100) ),
    'slice2':		        ( '%c[:%p]',
                                  (0, 'expr'),
                                  (1, 100) ),
    'slice3':		            ( '%c[%p:%p]',
                                  (0, 'expr'),
                                  (1, 100), (2, 100) ),

    'IMPORT_FROM':              ( '%{pattr}', ),
    'attribute':	        ( '%c.%[1]{pattr}',
                                  (0, 'expr')),
    'LOAD_STR':	                ( '%{pattr}', ),
    'LOAD_FAST':	        ( '%{pattr}', ),
    'LOAD_NAME':	        ( '%{pattr}', ),
    'LOAD_CLASSNAME':	        ( '%{pattr}', ),
    'LOAD_GLOBAL':	        ( '%{pattr}', ),
    'LOAD_DEREF':	        ( '%{pattr}', ),
    'LOAD_LOCALS':	        ( 'locals()', ),
    'LOAD_ASSERT':              ( '%{pattr}', ),
    'DELETE_FAST':	        ( '%|del %{pattr}\n', ),
    'DELETE_NAME':	        ( '%|del %{pattr}\n', ),
    'DELETE_GLOBAL':	        ( '%|del %{pattr}\n', ),
    'delete_subscript':         ( '%|del %p[%c]\n',
                                  (0, 'expr', PRECEDENCE['subscript']), (1, 'expr') ),
    'subscript':                ( '%p[%c]',
                                      (0, 'expr', PRECEDENCE['subscript']),
                                      (1, 'expr') ),
    'subscript2':               ( '%p[%c]',
                                      (0, 'expr', PRECEDENCE['subscript']),
                                      (1, 'expr') ),
    'store_subscript':	        ( '%p[%c]',
                                  (0, 'expr', PRECEDENCE['subscript']),
                                  (1, 'expr') ),
    'STORE_FAST':	        ( '%{pattr}', ),
    'STORE_NAME':	        ( '%{pattr}', ),
    'STORE_GLOBAL':	        ( '%{pattr}', ),
    'STORE_DEREF':	        ( '%{pattr}', ),
    'unpack':		        ( '%C%,', (1, maxint, ', ') ),

    # This nonterminal we create on the fly in semantic routines
    'unpack_w_parens':	        ( '(%C%,)', (1, maxint, ', ') ),

    # This nonterminal we create on the fly in semantic routines
    'attribute_w_parens':	( '(%c).%[1]{pattr}',
                                  (0, 'expr')),

    'unpack_list':	        ( '[%C]',
                                      (1, maxint, ', ') ),
    'build_tuple2':	        ( '%P',
                                      (0, -1, ', ', 100) ),

    'list_iter':	    ( '%c', 0 ),
    'list_for':		    ( ' for %c in %c%c', 2, 0, 3 ),
    'list_if':		    ( ' if %p%c',
                              (0, 'expr', 27), 2 ),
    'list_if_not':	    ( ' if not %p%c',
                              (0, 'expr', PRECEDENCE['unary_not']),
                              2 ),
    'lc_body':		    ( '', ),	# ignore when recursing

    'comp_iter':	    ( '%c', 0 ),
    'comp_if':		    ( ' if %c%c', 0, 2 ),
    'comp_if_not':	    ( ' if not %p%c',
                              (0, 'expr', PRECEDENCE['unary_not']), 2 ),
    'comp_body':	    ( '', ),	# ignore when recusing
    'set_comp_body':        ( '%c', 0 ),
    'gen_comp_body':        ( '%c', 0 ),
    'dict_comp_body':       ( '%c:%c', 1, 0 ),

    'assign':		    ( '%|%c = %p\n', -1, (0, 200) ),

    # The 2nd parameter should have a = suffix.
    # There is a rule with a 4th parameter "store"
    # which we don't use here.
    'aug_assign1':      ( '%|%c %c %c\n', 0, 2, 1),

    'aug_assign2':	    ( '%|%c.%[2]{pattr} %c %c\n', 0, -3, -4 ),
    'designList':	    ( '%c = %c', 0, -1 ),
    'and':          	( '%c and %c', 0, 2 ),
    'ret_and':        	( '%c and %c', 0, 2 ),
    'and2':          	( '%c', 3 ),
    'or':           	( '%c or %c', 0, 2 ),
    'ret_or':           ( '%c or %c', 0, 2 ),
    'conditional':      ( '%p if %c else %c',
                          (2, 'expr', 27), 0, 4 ),
    'if_expr_lambda':   ( '%p if %c else %c',
                          (2, 'expr', 27), (0, 'expr'), 4 ),
    'if_expr_true':     ( '%p if 1 else %c', (0, 'expr', 27), 2 ),
    'ret_cond':         ( '%p if %p else %p', (2, 27), (0, 27), (-1, 27) ),
    'conditional_not':  ( '%p if not %p else %p',
                          (2, 27),
                          (0, "expr", PRECEDENCE['unary_not']),
                          (4, 27) ),
    'conditional_not_lambda':
                        ( '%p if not %c else %c',
                          (2, 'expr', 27), 0, 4 ),

    'compare_single':	    ( '%p %[-1]{pattr.replace("-", " ")} %p', (0, 19), (1, 19) ),
    'compare_chained':	    ( '%p %p', (0, 29), (1, 30)),
    'compare_chained1':	    ( '%[3]{pattr.replace("-", " ")} %p %p', (0, 19), (-2, 19)),
    'compare_chained2':	    ( '%[1]{pattr.replace("-", " ")} %p', (0, 19)),
#   'classdef': 	(), # handled by n_classdef()

    # A custom rule in n_function def distinguishes whether to call this or
    # function_def_async
    'function_def':         ( '\n\n%|def %c\n', -2), # -2 to handle closures

    'function_def_deco':    ( '\n\n%c', 0),
    'mkfuncdeco':  	    ( '%|@%c\n%c', 0, 1),

    # A custom rule in n_function def distinguishes whether to call this or
    # function_def_async
    'mkfuncdeco0':  	    ( '%|def %c\n', 0),

    'classdefdeco':  	    ( '\n\n%c', 0),
    'classdefdeco1':  	    ( '%|@%c\n%c', 0, 1),
    'kwarg':    	    ( '%[0]{pattr}=%c', 1),  # Change when Python 2 does LOAD_STR
    'kwargs':    	    ( '%D', (0, maxint, ', ') ),
    'kwargs1':    	    ( '%D', (0, maxint, ', ') ),

    'assert_expr_or':   ( '%c or %c', 0, 2 ),
    'assert_expr_and':  ( '%c and %c', 0, 2 ),
    'print_items_stmt': ( '%|print %c%c,\n', 0, 2 ),  # Python 2 only
    'print_items_nl_stmt': ( '%|print %c%c\n', 0, 2 ),
    'print_item':       ( ', %c', 0),
    'print_nl':	        ( '%|print\n', ),
    'print_to':		    ( '%|print >> %c, %c,\n', 0, 1 ),
    'print_to_nl':	    ( '%|print >> %c, %c\n', 0, 1 ),
    'print_nl_to':	    ( '%|print >> %c\n', 0 ),
    'print_to_items':	( '%C', (0, 2, ', ') ),

    'call_stmt':	    ( '%|%p\n', (0, 200)),
    'break':	            ( '%|break\n', ),
    'continue':	            ( '%|continue\n', ),

    'raise_stmt0':	    ( '%|raise\n', ),
    'raise_stmt1':	    ( '%|raise %c\n', 0),
    'raise_stmt3':	    ( '%|raise %c, %c, %c\n', 0, 1, 2),
#    'yield':	        ( 'yield %c', 0),
#    'return':	        ( '%|return %c\n', 0),
    'return_if_stmt':	( 'return %c\n', 0),

    'ifstmt':		( '%|if %c:\n%+%c%-',
                            0, # "testexpr" or "testexpr_then"
                            1, # "_ifstmts_jump" or "return_stmts"
                        ),

    'iflaststmt':	( '%|if %c:\n%+%c%-', 0, 1 ),
    'iflaststmtl':		( '%|if %c:\n%+%c%-', 0, 1 ),
    'testtrue':         ( 'not %p',
                          (0, PRECEDENCE['unary_not']) ),

    # Generally the args here are 0: (some sort of) "testexpr",
    #                             1: (some sort of) "cstmts_opt",
    #                             2 or 3: "else_suite"
    # But unfortunately there are irregularities, For example, 2.6- uses "testexpr_then"
    # and sometimes "cstmts" instead of "cstmts_opt" happens.
    # Down the line we might isolate these into version-specific rules.
    'ifelsestmt':	( '%|if %c:\n%+%c%-%|else:\n%+%c%-', 0, 1, 3 ),
    'ifelsestmtc':	( '%|if %c:\n%+%c%-%|else:\n%+%c%-', 0, 1, 3 ),
    'ifelsestmtl':	( '%|if %c:\n%+%c%-%|else:\n%+%c%-', 0, 1, 3 ),

    #  These are created only via transformation
    'ifelifstmt':	( '%|if %c:\n%+%c%-%c',
                          0, # "testexpr" or "testexpr_then"
                          1, 3 ),
    'elifelifstmt':	( '%|elif %c:\n%+%c%-%c', 0, 1, 3 ),
    'elifstmt':		( '%|elif %c:\n%+%c%-', 0, 1 ),
    'elifelsestmt':	( '%|elif %c:\n%+%c%-%|else:\n%+%c%-', 0, 1, 3 ),
    'ifelsestmtr':	( '%|if %c:\n%+%c%-%|else:\n%+%c%-', 0, 1, 2 ),
    'ifelsestmtr2':	( '%|if %c:\n%+%c%-%|else:\n%+%c%-\n\n', 0, 1, 3 ), # has COME_FROM
    'elifelsestmtr':	( '%|elif %c:\n%+%c%-%|else:\n%+%c%-\n\n', 0, 1, 2 ),
    'elifelsestmtr2':	( '%|elif %c:\n%+%c%-%|else:\n%+%c%-\n\n', 0, 1, 3 ), # has COME_FROM

    'whileTruestmt':	( '%|while True:\n%+%c%-\n\n', 1 ),
    'whilestmt':	    ( '%|while %c:\n%+%c%-\n\n', 1, 2 ),
    'while1stmt':	    ( '%|while 1:\n%+%c%-\n\n', 1 ),
    'while1elsestmt':   ( '%|while 1:\n%+%c%-%|else:\n%+%c%-\n\n', 1, -2 ),
    'whileelsestmt':	( '%|while %c:\n%+%c%-%|else:\n%+%c%-\n\n', 1, 2, -2 ),
    'whileelsestmt2':	( '%|while %c:\n%+%c%-%|else:\n%+%c%-\n\n', 1, 2, -3 ),
    'whileelselaststmt':	( '%|while %c:\n%+%c%-%|else:\n%+%c%-', 1, 2, -2 ),

    # Note: Python 3.8+ changes this
    'for':              ( '%|for %c in %c:\n%+%c%-\n\n',
                          (3, 'store'),
                          (1, 'expr'),
                          (4, 'for_block') ),
    'forelsestmt':	    (
        '%|for %c in %c:\n%+%c%-%|else:\n%+%c%-\n\n',
                          (3, 'store'),
                          (1, 'expr'),
                          (4, 'for_block'), -2 ),
    'forelselaststmt':	(
        '%|for %c in %c:\n%+%c%-%|else:\n%+%c%-',
                          (3, 'store'),
                          (1, 'expr'),
                          (4, 'for_block'), -2 ),
    'forelselaststmtl':	(
        '%|for %c in %c:\n%+%c%-%|else:\n%+%c%-\n\n',
                          (3, 'store'),
                          (1, 'expr'),
                          (4, 'for_block'), -2 ),

    'try_except':       ( '%|try:\n%+%c%-%c\n\n', 1, 3 ),
    'tryelsestmt':	    ( '%|try:\n%+%c%-%c%|else:\n%+%c%-\n\n', 1, 3, 4 ),
    'tryelsestmtc':	    ( '%|try:\n%+%c%-%c%|else:\n%+%c%-', 1, 3, 4 ),
    'tryelsestmtl':	    ( '%|try:\n%+%c%-%c%|else:\n%+%c%-', 1, 3, 4 ),
    'tf_try_except':	( '%c%-%c%+', 1, 3 ),
    'tf_tryelsestmt':	( '%c%-%c%|else:\n%+%c', 1, 3, 4 ),
    'tryfinallystmt':	( '%|try:\n%+%c%-%|finally:\n%+%c%-\n\n', 1, 5 ),
    'except':           ( '%|except:\n%+%c%-', 3 ),
    'except_cond1':	( '%|except %c:\n', (1, 'expr') ),
    'except_cond2':     ( '%|except %c as %c:\n',
                          (1, 'expr'), (5, 'store') ),
    'except_suite':     ( '%+%c%-%C', 0, (1, maxint, '') ),

    # In Python 3.6+, this is more complicated in the presence of "returns"
    'except_suite_finalize':     ( '%+%c%-%C', 1, (3, maxint, '') ),

    'pass':	            ( '%|pass\n', ),
    'STORE_FAST':	    ( '%{pattr}', ),
    'kv':		    ( '%c: %c', 3, 1 ),
    'kv2':		    ( '%c: %c', 1, 2 ),
    'import':               ( '%|import %c\n', 2),
    'importlist':           ( '%C', (0, maxint, ', ') ),
    'import_from':          ( '%|from %[2]{pattr} import %c\n',
                              (3, 'importlist') ),
    'import_from_star':     ( '%|from %[2]{pattr} import *\n', ),
}


MAP_DIRECT = (TABLE_DIRECT, )
MAP_R0 = (TABLE_R0, -1, 0)
MAP_R = (TABLE_R, -1)

MAP = {
    'stmt':		MAP_R,
    'call':	        MAP_R,
    'del_stmt':		MAP_R,
    'store':	        MAP_R,
    'exprlist':		MAP_R0,
}

ASSIGN_TUPLE_PARAM = lambda param_name: \
             SyntaxTree('expr', [ Token('LOAD_FAST', pattr=param_name) ])

escape = re.compile(r'''
            (?P<prefix> [^%]* )
            % ( \[ (?P<child> -? \d+ ) \] )?
                ((?P<type> [^{] ) |
                 ( [{] (?P<expr> [^}]* ) [}] ))
        ''', re.VERBOSE)
