#  Copyright (c) 2018 by Rocky Bernstein
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

"""Isolate Python version-specific semantic actions here.
"""

from uncompyle6.semantics.consts import (
    INDENT_PER_LEVEL, TABLE_R, TABLE_DIRECT)

from uncompyle6.semantics.make_function import (
    make_function3_annotate,
    )

from xdis.util import COMPILER_FLAG_BIT
from xdis.code import iscode
from uncompyle6.parsers.astnode import AST
from uncompyle6.scanners.tok import Token
from uncompyle6.semantics.helper import flatten_list

def customize_for_version(self, is_pypy, version):
    if is_pypy:
        ########################
        # PyPy changes
        #######################
        TABLE_DIRECT.update({
            'assert_pypy':	( '%|assert %c\n' , 1 ),
            'assert2_pypy':	( '%|assert %c, %c\n' , 1, 4 ),
            'try_except_pypy':	   ( '%|try:\n%+%c%-%c\n\n', 1, 2 ),
            'tryfinallystmt_pypy': ( '%|try:\n%+%c%-%|finally:\n%+%c%-\n\n', 1, 3 ),
            'assign3_pypy':        ( '%|%c, %c, %c = %c, %c, %c\n', 5, 4, 3, 0, 1, 2 ),
            'assign2_pypy':        ( '%|%c, %c = %c, %c\n', 3, 2, 0, 1),
            })
    else:
        ########################
        # Without PyPy
        #######################
        TABLE_DIRECT.update({
            'assert':		( '%|assert %c\n' , 0 ),
            'assert2':		( '%|assert %c, %c\n' , 0, 3 ),
            'try_except':	( '%|try:\n%+%c%-%c\n\n', 1, 3 ),
            'assign2':      ( '%|%c, %c = %c, %c\n', 3, 4, 0, 1 ),
            'assign3':      ( '%|%c, %c, %c = %c, %c, %c\n', 5, 6, 7, 0, 1, 2 ),
            })
    if version < 3.0:
        TABLE_R.update({
            'STORE_SLICE+0':	( '%c[:]', 0 ),
            'STORE_SLICE+1':	( '%c[%p:]', 0, (1, -1) ),
            'STORE_SLICE+2':	( '%c[:%p]', 0, (1, -1) ),
            'STORE_SLICE+3':	( '%c[%p:%p]', 0, (1, -1), (2, -1) ),
            'DELETE_SLICE+0':	( '%|del %c[:]\n', 0 ),
            'DELETE_SLICE+1':	( '%|del %c[%c:]\n', 0, 1 ),
            'DELETE_SLICE+2':	( '%|del %c[:%c]\n', 0, 1 ),
            'DELETE_SLICE+3':	( '%|del %c[%c:%c]\n', 0, 1, 2 ),
        })
        TABLE_DIRECT.update({
            'raise_stmt2':	( '%|raise %c, %c\n', 0, 1),
        })

        # exec as a built-in statement is only in Python 2.x
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
        self.n_exec_smt = n_exec_stmt

    else:
        TABLE_DIRECT.update({
            # Gotta love Python for its futzing around with syntax like this
            'raise_stmt2':	 ( '%|raise %c from %c\n', 0, 1),
        })

        if version >= 3.2:
            TABLE_DIRECT.update({
            'del_deref_stmt': ( '%|del %c\n', 0),
            'DELETE_DEREF': ( '%{pattr}', 0 ),
            })

    if version <= 2.4:
        TABLE_DIRECT.update({
            'importmultiple': ( '%|import %c%c\n', 2, 3),
            'import_cont'   : ( ', %c', 2),
            'tryfinallystmt': ( '%|try:\n%+%c%-%|finally:\n%+%c%-',
                                (1, 'suite_stmts_opt') ,
                                (5, 'suite_stmts_opt') )
            })
        if version == 2.3:
            TABLE_DIRECT.update({
                'if1_stmt':	( '%|if 1\n%+%c%-', 5 )
            })

        global NAME_MODULE
        NAME_MODULE = AST('stmt',
                          [ AST('assign',
                                [ AST('expr',
                                      [Token('LOAD_GLOBAL', pattr='__name__',
                                             offset=0, has_arg=True)]),
                                  AST('store',
                                      [ Token('STORE_NAME', pattr='__module__',
                                              offset=3, has_arg=True)])
                                ])])
        pass
        if version <= 2.3:
            if version <= 2.1:
                TABLE_DIRECT.update({
                    'importmultiple': ( '%c', 2 ),
                    # FIXME: not quite right. We have indiividual imports
                    # when there is in fact one: "import a, b, ..."
                    'imports_cont': ( '%C%,', (1, 100, '\n') ),
                })
                pass
            pass
        pass
    elif version >= 2.5:
        ########################
        # Import style for 2.5+
        ########################
        TABLE_DIRECT.update({
            'importmultiple': ( '%|import %c%c\n', 2, 3 ),
            'import_cont'   : ( ', %c', 2 ),
            # With/as is allowed as "from future" thing in 2.5
            # Note: It is safe to put the variables after "as" in parenthesis,
            # and sometimes it is needed.
            'withstmt':     ( '%|with %c:\n%+%c%-', 0, 3),
            'withasstmt':   ( '%|with %c as (%c):\n%+%c%-', 0, 2, 3),
        })

        # In 2.5+ "except" handlers and the "finally" can appear in one
        # "try" statement. So the below has the effect of combining the
        # "tryfinally" with statement with the "try_except" statement
        def tryfinallystmt(node):
            if len(node[1][0]) == 1 and node[1][0][0] == 'stmt':
                if node[1][0][0][0] == 'try_except':
                    node[1][0][0][0].kind = 'tf_try_except'
                if node[1][0][0][0] == 'tryelsestmt':
                    node[1][0][0][0].kind = 'tf_tryelsestmt'
            self.default(node)
        self.n_tryfinallystmt = tryfinallystmt

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
            'function_def_annotate': ( '\n\n%|def %c%c\n', -1, 0),
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

            self.indent_more()
            for annotate_last in range(len(node)-1, -1, -1):
                if node[annotate_last] == 'annotate_tuple':
                    break

            # FIXME: the real situation is that when derived from
            # function_def_annotate we the name has been filled in.
            # But when derived from funcdefdeco it hasn't Would like a better
            # way to distinquish.
            if self.f.getvalue()[-4:] == 'def ':
                self.write(code.attr.co_name)

            # FIXME: handle and pass full annotate args
            make_function3_annotate(self, node, is_lambda=False,
                                    codeNode=code, annotate_last=annotate_last)

            if len(self.param_stack) > 1:
                self.write('\n\n')
            else:
                self.write('\n\n\n')
            self.indent_less()
            self.prune() # stop recursing
        self.n_mkfunc_annotate = n_mkfunc_annotate

        if version >= 3.4:
            ########################
            # Python 3.4+ Additions
            #######################
            TABLE_DIRECT.update({
                'LOAD_CLASSDEREF':	( '%{pattr}', ),
                })
            ########################
            # Python 3.5+ Additions
            #######################
            if version >= 3.5:
                TABLE_DIRECT.update({
                    'await_expr':	       ( 'await %c', 0),
                    'await_stmt':	       ( '%|%c\n', 0),
                    'async_for_stmt':      (
                        '%|async for %c in %c:\n%+%c%-\n\n', 9, 1, 25 ),
                    'async_forelse_stmt':  (
                        '%|async for %c in %c:\n%+%c%-%|else:\n%+%c%-\n\n', 9, 1, 25, 28 ),
                    'async_with_stmt':     (
                        '%|async with %c:\n%+%c%-', 0, 7),
                    'async_with_as_stmt':  (
                        '%|async with %c as %c:\n%+%c%-', 0, 6, 7),
                    'unmap_dict':	       ( '{**%C}', (0, -1, ', **') ),
                    # 'unmapexpr':	       ( '{**%c}', 0), # done by n_unmapexpr

                })

                def async_call(node):
                    self.f.write('async ')
                    node.kind == 'call'
                    p = self.prec
                    self.prec = 80
                    self.template_engine(('%c(%P)', 0, (1, -4, ', ',
                                          100)), node)
                    self.prec = p
                    node.kind == 'async_call'
                    self.prune()
                self.n_async_call = async_call
                self.n_build_list_unpack = self.n_list

                if version == 3.5:
                    def n_call(node):
                        mapping = self._get_mapping(node)
                        table = mapping[0]
                        key = node
                        for i in mapping[1:]:
                            key = key[i]
                            pass
                        if key.kind.startswith('CALL_FUNCTION_VAR_KW'):
                            # Python 3.5 changes the stack position of *args. kwargs come
                            # after *args whereas in earlier Pythons, *args is at the end
                            # which simplifies things from our perspective.
                            # Python 3.6+ replaces CALL_FUNCTION_VAR_KW with CALL_FUNCTION_EX
                            # We will just swap the order to make it look like earlier Python 3.
                            entry = table[key.kind]
                            kwarg_pos = entry[2][1]
                            args_pos = kwarg_pos - 1
                            # Put last node[args_pos] after subsequent kwargs
                            while node[kwarg_pos] == 'kwarg' and kwarg_pos < len(node):
                                # swap node[args_pos] with node[kwargs_pos]
                                node[kwarg_pos], node[args_pos] = node[args_pos], node[kwarg_pos]
                                args_pos = kwarg_pos
                                kwarg_pos += 1
                        elif key.kind.startswith('CALL_FUNCTION_VAR'):
                            nargs = node[-1].attr & 0xFF
                            if nargs > 0:
                                template = ('%c(%C, ', 0, (1, nargs+1, ', '))
                            else:
                                template = ('%c(', 0)
                            self.template_engine(template, node)

                            args_node =  node[-2]
                            if args_node == 'pos_arg':
                                args_node = args_node[0]
                            if args_node == 'expr':
                                args_node = args_node[0]
                            if args_node == 'build_list_unpack':
                                template = ('*%P)', (0, len(args_node)-1, ', *', 100))
                                self.template_engine(template, args_node)
                            else:
                                template = ('*%c)', -2)
                                self.template_engine(template, node)
                            self.prune()

                        self.default(node)
                    self.n_call = n_call

                def n_function_def(node):
                    if self.version == 3.6:
                        code_node = node[0][0]
                    else:
                        code_node = node[0][1]

                    is_code = hasattr(code_node, 'attr') and iscode(code_node.attr)
                    if (is_code and
                        (code_node.attr.co_flags & COMPILER_FLAG_BIT['COROUTINE'])):
                        self.template_engine(('\n\n%|async def %c\n',
                                              -2), node)
                    else:
                        self.template_engine(('\n\n%|def %c\n', -2),
                                             node)
                    self.prune()
                self.n_function_def = n_function_def

                def unmapexpr(node):
                    last_n = node[0][-1]
                    for n in node[0]:
                        self.preorder(n)
                        if n != last_n:
                            self.f.write(', **')
                            pass
                        pass
                    self.prune()
                    pass
                self.n_unmapexpr = unmapexpr

            if version >= 3.6:
                ########################
                # Python 3.6+ Additions
                #######################

                TABLE_DIRECT.update({
                    'tryfinally36':  ( '%|try:\n%+%c%-%|finally:\n%+%c%-\n\n',
                                       (1, 'returns'), 3 ),
                    'fstring_expr':   ( "{%c%{conversion}}", 0),
                    'fstring_single': ( "f'{%c%{conversion}}'", 0),
                    'fstring_multi':  ( "f'%c'", 0),
                    'func_args36':    ( "%c(**", 0),
                    'try_except36':   ( '%|try:\n%+%c%-%c\n\n', 1, 2 ),
                    'unpack_list':    ( '*%c', (0, 'list') ),
                    'call_ex' : (
                        '%c(%c)',
                        (0, 'expr'), 1),
                    'call_ex_kw' : (
                        '%c(%c)',
                        (0, 'expr'), 2),

                })

                TABLE_R.update({
                    'CALL_FUNCTION_EX': ('%c(*%P)', 0, (1, 2, ', ', 100)),
                    # Not quite right
                    'CALL_FUNCTION_EX_KW': ('%c(**%C)', 0, (2, 3, ',')),
                    })

                def build_unpack_tuple_with_call(node):

                    if node[0] == 'expr':
                        tup = node[0][0]
                    else:
                        tup = node[0]
                        pass
                    assert tup == 'tuple'
                    self.call36_tuple(tup)

                    buwc = node[-1]
                    assert buwc.kind.startswith('BUILD_TUPLE_UNPACK_WITH_CALL')
                    for n in node[1:-1]:
                        self.f.write(', *')
                        self.preorder(n)
                        pass
                    self.prune()
                    return
                self.n_build_tuple_unpack_with_call = build_unpack_tuple_with_call

                def build_unpack_map_with_call(node):
                    n = node[0]
                    if n == 'expr':
                        n = n[0]
                    if n == 'dict':
                        self.call36_dict(n)
                        first = 1
                        sep = ', **'
                    else:
                        first = 0
                        sep = '**'
                    for n in node[first:-1]:
                        self.f.write(sep)
                        self.preorder(n)
                        sep = ', **'
                        pass
                    self.prune()
                    return
                self.n_build_map_unpack_with_call = build_unpack_map_with_call

                def call_ex_kw2(node):
                    """Handle CALL_FUNCTION_EX 2  (have KW) but with
                    BUILD_{MAP,TUPLE}_UNPACK_WITH_CALL"""

                    # This is weird shit. Thanks Python!
                    self.preorder(node[0])
                    self.write('(')

                    assert node[1] == 'build_tuple_unpack_with_call'
                    btuwc = node[1]
                    tup = btuwc[0]
                    if tup == 'expr':
                        tup = tup[0]
                    assert tup == 'tuple'
                    self.call36_tuple(tup)
                    assert node[2] == 'build_map_unpack_with_call'

                    self.write(', ')
                    d = node[2][0]
                    if d == 'expr':
                        d = d[0]
                    assert d == 'dict'
                    self.call36_dict(d)

                    args = btuwc[1]
                    self.write(', *')
                    self.preorder(args)

                    self.write(', **')
                    star_star_args = node[2][1]
                    if star_star_args == 'expr':
                        star_star_args = star_star_args[0]
                    self.preorder(star_star_args)
                    self.write(')')
                    self.prune()
                self.n_call_ex_kw2 = call_ex_kw2

                def call_ex_kw3(node):
                    """Handle CALL_FUNCTION_EX 1 (have KW) but without
                    BUILD_MAP_UNPACK_WITH_CALL"""
                    self.preorder(node[0])
                    self.write('(')
                    args = node[1][0]
                    if args == 'expr':
                        args = args[0]
                    if args == 'tuple':
                        if self.call36_tuple(args) > 0:
                            self.write(', ')
                            pass
                        pass

                    self.write('*')
                    self.preorder(node[1][1])
                    self.write(', ')

                    kwargs = node[2]
                    if kwargs == 'expr':
                        kwargs = kwargs[0]
                    self.write('**')
                    self.preorder(kwargs)
                    self.write(')')
                    self.prune()
                self.n_call_ex_kw3 = call_ex_kw3

                def call_ex_kw4(node):
                    """Handle CALL_FUNCTION_EX 2  (have KW) but without
                    BUILD_{MAP,TUPLE}_UNPACK_WITH_CALL"""
                    self.preorder(node[0])
                    self.write('(')
                    args = node[1][0]
                    if args == 'tuple':
                        if self.call36_tuple(args) > 0:
                            self.write(', ')
                            pass
                        pass
                    else:
                        self.write('*')
                        self.preorder(args)
                        self.write(', ')
                        pass

                    kwargs = node[2]
                    if kwargs == 'expr':
                        kwargs = kwargs[0]
                    self.write('**')
                    self.preorder(kwargs)
                    self.write(')')
                    self.prune()
                self.n_call_ex_kw4 = call_ex_kw4

                def call36_tuple(node):
                    """
                    A tuple used in a call, these are like normal tuples but they
                    don't have the enclosing parenthesis.
                    """
                    assert node == 'tuple'
                    # Note: don't iterate over last element which is a
                    # BUILD_TUPLE...
                    flat_elems = flatten_list(node[:-1])

                    self.indent_more(INDENT_PER_LEVEL)
                    sep = ''

                    for elem in flat_elems:
                        if elem in ('ROT_THREE', 'EXTENDED_ARG'):
                            continue
                        assert elem == 'expr'
                        line_number = self.line_number
                        value = self.traverse(elem)
                        if line_number != self.line_number:
                            sep += '\n' + self.indent + INDENT_PER_LEVEL[:-1]
                        self.write(sep, value)
                        sep = ', '

                    self.indent_less(INDENT_PER_LEVEL)
                    return len(flat_elems)
                self.call36_tuple = call36_tuple

                def call36_dict(node):
                    """
                    A dict used in a call_ex_kw2, which are a dictionary items expressed
                    in a call. This should format to:
                         a=1, b=2
                    In other words, no braces, no quotes around keys and ":" becomes
                    "=".

                    We will source-code use line breaks to guide us when to break.
                    """
                    p = self.prec
                    self.prec = 100

                    self.indent_more(INDENT_PER_LEVEL)
                    sep = INDENT_PER_LEVEL[:-1]
                    line_number = self.line_number

                    if  node[0].kind.startswith('kvlist'):
                        # Python 3.5+ style key/value list in dict
                        kv_node = node[0]
                        l = list(kv_node)
                        i = 0
                        # Respect line breaks from source
                        while i < len(l):
                            self.write(sep)
                            name = self.traverse(l[i], indent='')
                            # Strip off beginning and trailing quotes in name
                            name = name[1:-1]
                            if i > 0:
                                line_number = self.indent_if_source_nl(line_number,
                                                                       self.indent + INDENT_PER_LEVEL[:-1])
                            line_number = self.line_number
                            self.write(name, '=')
                            value = self.traverse(l[i+1], indent=self.indent+(len(name)+2)*' ')
                            self.write(value)
                            sep = ", "
                            if line_number != self.line_number:
                                sep += "\n" + self.indent + INDENT_PER_LEVEL[:-1]
                                line_number = self.line_number
                            i += 2
                            pass
                    elif node[-1].kind.startswith('BUILD_CONST_KEY_MAP'):
                        keys_node = node[-2]
                        keys = keys_node.attr
                        # from trepan.api import debug; debug()
                        assert keys_node == 'LOAD_CONST' and isinstance(keys, tuple)
                        for i in range(node[-1].attr):
                            self.write(sep)
                            self.write(keys[i], '=')
                            value = self.traverse(node[i], indent='')
                            self.write(value)
                            sep = ", "
                            if line_number != self.line_number:
                                sep += "\n" + self.indent + INDENT_PER_LEVEL[:-1]
                                line_number = self.line_number
                                pass
                            pass
                    else:
                        assert False, "Don't known to to untangle dictionary"

                    self.prec = p
                    self.indent_less(INDENT_PER_LEVEL)
                    return
                self.call36_dict = call36_dict


                FSTRING_CONVERSION_MAP = {1: '!s', 2: '!r', 3: '!a'}

                def f_conversion(node):
                    node.conversion = FSTRING_CONVERSION_MAP.get(node.data[1].attr, '')

                def fstring_expr(node):
                    f_conversion(node)
                    self.default(node)
                self.n_fstring_expr = fstring_expr

                def fstring_single(node):
                    f_conversion(node)
                    self.default(node)
                self.n_fstring_single = fstring_single

                # def kwargs_only_36(node):
                #     keys = node[-1].attr
                #     num_kwargs = len(keys)
                #     values = node[:num_kwargs]
                #     for i, (key, value) in enumerate(zip(keys, values)):
                #         self.write(key + '=')
                #         self.preorder(value)
                #         if i < num_kwargs:
                #             self.write(',')
                #     self.prune()
                #     return
                # self.n_kwargs_only_36 = kwargs_only_36

                def kwargs_36(node):
                    self.write('(')
                    keys = node[-1].attr
                    num_kwargs = len(keys)
                    num_posargs = len(node) - (num_kwargs + 1)
                    n = len(node)
                    assert n >= len(keys)+1, \
                      'not enough parameters keyword-tuple values'
                    # try:
                    #     assert n >= len(keys)+1, \
                    #         'not enough parameters keyword-tuple values'
                    # except:
                    #     from trepan.api import debug; debug()
                    sep = ''
                    # FIXME: adjust output for line breaks?
                    for i in range(num_posargs):
                        self.write(sep)
                        self.preorder(node[i])
                        sep = ', '

                    i = num_posargs
                    j = 0
                    # FIXME: adjust output for line breaks?
                    while i < n-1:
                        self.write(sep)
                        self.write(keys[j] + '=')
                        self.preorder(node[i])
                        sep=', '
                        i += 1
                        j += 1
                    self.write(')')
                    self.prune()
                    return
                self.n_kwargs_36 = kwargs_36

                def starred(node):
                    l = len(node)
                    assert l > 0
                    pos_args = node[0]
                    if pos_args == 'expr':
                        pos_args = pos_args[0]
                    if pos_args == 'tuple':
                        star_start = 1
                        template = '%C', (0, -1, ', ')
                        self.template_engine(template, pos_args)
                        self.write(', ')
                    else:
                        star_start = 0
                    if l > 1:
                        template = ( '*%C', (star_start, -1, ', *') )
                    else:
                        template = ( '*%c', (star_start, 'expr') )
                    self.template_engine(template, node)
                    self.prune()

                self.n_starred = starred

                def return_closure(node):
                    # Nothing should be output here
                    self.prune()
                    return
                self.n_return_closure = return_closure
                pass # version >= 3.6
            pass # version >= 3.4
        pass # version >= 3.0
    return
