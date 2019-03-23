#  Copyright (c) 2018-2019 by Rocky Bernstein
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

"""Isolate Python 3 version-specific semantic actions here.
"""

from uncompyle6.semantics.consts import (
    INDENT_PER_LEVEL, PRECEDENCE, TABLE_DIRECT, TABLE_R)

from xdis.code import iscode
from xdis.util import COMPILER_FLAG_BIT
from spark_parser.ast import GenericASTTraversalPruningException
from uncompyle6.scanners.tok import Token
from uncompyle6.semantics.helper import flatten_list
from uncompyle6.semantics.make_function import make_function3_annotate

def customize_for_version3(self, version):
    TABLE_DIRECT.update({
        'function_def_annotate': ( '\n\n%|def %c%c\n', -1, 0),
        'store_locals': ( '%|# inspect.currentframe().f_locals = __locals__\n', ),
        })

    assert version >= 3.0

    def n_classdef3(node):
        # class definition ('class X(A,B,C):')
        cclass = self.currentclass

        # Pick out various needed bits of information
        # * class_name - the name of the class
        # * subclass_info - the parameters to the class  e.g.
        #      class Foo(bar, baz)
        #               ----------
        # * subclass_code - the code for the subclass body
        subclass_info = None
        if node == 'classdefdeco2':
            if self.version >= 3.6:
                class_name = node[1][1].pattr
            elif self.version <= 3.3:
                class_name = node[2][0].pattr
            else:
                class_name = node[1][2].pattr
            build_class = node
        else:
            build_class = node[0]
            if self.version >= 3.6:
                if build_class == 'build_class_kw':
                    mkfunc = build_class[1]
                    assert mkfunc == 'mkfunc'
                    subclass_info = build_class
                    if hasattr(mkfunc[0], 'attr') and iscode(mkfunc[0].attr):
                        subclass_code = mkfunc[0].attr
                    else:
                        assert mkfunc[0] == 'load_closure'
                        subclass_code = mkfunc[1].attr
                        assert iscode(subclass_code)
                if build_class[1][0] == 'load_closure':
                    code_node = build_class[1][1]
                else:
                    code_node = build_class[1][0]
                class_name = code_node.attr.co_name
            else:
                class_name = node[1][0].pattr
                build_class = node[0]

        assert 'mkfunc' == build_class[1]
        mkfunc = build_class[1]
        if mkfunc[0] in ('kwargs', 'no_kwargs'):
            if 3.0 <= self.version <= 3.2:
                for n in mkfunc:
                    if hasattr(n, 'attr') and iscode(n.attr):
                        subclass_code = n.attr
                        break
                    elif n == 'expr':
                        subclass_code = n[0].attr
                    pass
                pass
            else:
                for n in mkfunc:
                    if hasattr(n, 'attr') and iscode(n.attr):
                        subclass_code = n.attr
                        break
                    pass
                pass
            if node == 'classdefdeco2':
                subclass_info = node
            else:
                subclass_info = node[0]
        elif build_class[1][0] == 'load_closure':
            # Python 3 with closures not functions
            load_closure = build_class[1]
            if hasattr(load_closure[-3], 'attr'):
                # Python 3.3 classes with closures work like this.
                # Note have to test before 3.2 case because
                # index -2 also has an attr.
                subclass_code = load_closure[-3].attr
            elif hasattr(load_closure[-2], 'attr'):
                # Python 3.2 works like this
                subclass_code = load_closure[-2].attr
            else:
                raise 'Internal Error n_classdef: cannot find class body'
            if hasattr(build_class[3], '__len__'):
                if not subclass_info:
                    subclass_info = build_class[3]
            elif hasattr(build_class[2], '__len__'):
                subclass_info = build_class[2]
            else:
                raise 'Internal Error n_classdef: cannot superclass name'
        elif self.version >= 3.6 and node == 'classdefdeco2':
            subclass_info = node
            subclass_code = build_class[1][0].attr
        elif not subclass_info:
            if mkfunc[0] in ('no_kwargs', 'kwargs'):
                subclass_code = mkfunc[1].attr
            else:
                subclass_code = mkfunc[0].attr
            if node == 'classdefdeco2':
                subclass_info = node
            else:
                subclass_info = node[0]

        if (node == 'classdefdeco2'):
            self.write('\n')
        else:
            self.write('\n\n')

        self.currentclass = str(class_name)
        self.write(self.indent, 'class ', self.currentclass)

        self.print_super_classes3(subclass_info)
        self.println(':')

        # class body
        self.indent_more()
        self.build_class(subclass_code)
        self.indent_less()

        self.currentclass = cclass
        if len(self.param_stack) > 1:
            self.write('\n\n')
        else:
            self.write('\n\n\n')

        self.prune()
    self.n_classdef3 = n_classdef3

    if version == 3.0:
        # In Python 3.0 there is code to move from _[dd] into
        # the iteration variable. These rules we can ignore
        # since we pick up the iteration variable some other way and
        # we definitely don't include in the source  _[dd].
        def n_comp_iter(node):
            if node[0] == 'expr':
                n = node[0][0]
                if (n == 'LOAD_FAST' and
                    n.pattr[0:2] == '_['):
                    self.prune()
                    pass
                pass
            # Not this special case, procede as normal...
            self.default(node)
        self.n_comp_iter = n_comp_iter

    if version >= 3.3:
        def n_yield_from(node):
            self.write('yield from')
            self.write(' ')
            if 3.3 <= self.version <= 3.4:
                self.preorder(node[0][0][0][0])
            elif self.version >= 3.5:
                self.preorder(node[0])
            else:
                assert False, "dunno about this python version"
            self.prune() # stop recursing
        self.n_yield_from = n_yield_from

    if 3.2 <= version <= 3.4:
        def n_call(node):
            mapping = self._get_mapping(node)
            key = node
            for i in mapping[1:]:
                key = key[i]
                pass
            if key.kind.startswith('CALL_FUNCTION_VAR_KW'):
                # We may want to fill this in...
                # But it is distinct from CALL_FUNCTION_VAR below
                pass
            elif key.kind.startswith('CALL_FUNCTION_VAR'):
                # CALL_FUNCTION_VAR's top element of the stack contains
                # the variable argument list, then comes
                # annotation args, then keyword args.
                # In the most least-top-most stack entry, but position 1
                # in node order, the positional args.
                argc = node[-1].attr
                nargs = argc & 0xFF
                kwargs = (argc >> 8) & 0xFF
                # FIXME: handle annotation args
                if kwargs != 0:
                    # kwargs == 0 is handled by the table entry
                    # Should probably handle it here though.
                    if nargs == 0:
                        template = ('%c(*%c, %C)',
                                    0, -2, (1, kwargs+1, ', '))
                    else:
                        template = ('%c(%C, *%c, %C)',
                                    0, (1, nargs+1, ', '),
                                    -2, (-2-kwargs, -2, ', '))
                    self.template_engine(template, node)
                    self.prune()

            self.default(node)
        self.n_call = n_call


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
                                code_node=code, annotate_last=annotate_last)

        if len(self.param_stack) > 1:
            self.write('\n\n')
        else:
            self.write('\n\n\n')
        self.indent_less()
        self.prune() # stop recursing
    self.n_mkfunc_annotate = n_mkfunc_annotate

    TABLE_DIRECT.update({
                'tryelsestmtl3': ( '%|try:\n%+%c%-%c%|else:\n%+%c%-',
                                   (1, 'suite_stmts_opt'),
                                   (3, 'except_handler'),
                                   (5, 'else_suitel') ),
        })
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
                    '%|async for %c in %c:\n%+%c%-%|else:\n%+%c%-\n\n',
                    9, 1, 25, (27, 'else_suite') ),
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
                        # Python 3.5 changes the stack position of
                        # *args: kwargs come after *args whereas
                        # in earlier Pythons, *args is at the end
                        # which simplifies things from our
                        # perspective.  Python 3.6+ replaces
                        # CALL_FUNCTION_VAR_KW with
                        # CALL_FUNCTION_EX We will just swap the
                        # order to make it look like earlier
                        # Python 3.
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
                        # CALL_FUNCTION_VAR's top element of the stack contains
                        # the variable argument list, then comes
                        # annotation args, then keyword args.
                        # In the most least-top-most stack entry, but position 1
                        # in node order, the positional args.
                        argc = node[-1].attr
                        nargs = argc & 0xFF
                        kwargs = (argc >> 8) & 0xFF
                        # FIXME: handle annotation args
                        if nargs > 0:
                            template = ('%c(%C, ', 0, (1, nargs+1, ', '))
                        else:
                            template = ('%c(', 0)
                        self.template_engine(template, node)

                        args_node =  node[-2]
                        if args_node in ('pos_arg', 'expr'):
                            args_node = args_node[0]
                        if args_node == 'build_list_unpack':
                            template = ('*%P)', (0, len(args_node)-1, ', *', 100))
                            self.template_engine(template, args_node)
                        else:
                            if len(node) - nargs > 3:
                                template = ('*%c, %C)', nargs+1, (nargs+kwargs+1, -1, ', '))
                            else:
                                template = ('*%c)', nargs+1)
                            self.template_engine(template, node)
                        self.prune()

                    self.default(node)
                self.n_call = n_call

            def n_function_def(node):
                if self.version >= 3.6:
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

            # FIXME: start here
            def n_list_unpack(node):
                """
                prettyprint an unpacked list or tuple
                """
                p = self.prec
                self.prec = 100
                lastnode = node.pop()
                lastnodetype = lastnode.kind

                # If this build list is inside a CALL_FUNCTION_VAR,
                # then the first * has already been printed.
                # Until I have a better way to check for CALL_FUNCTION_VAR,
                # will assume that if the text ends in *.
                last_was_star = self.f.getvalue().endswith('*')

                if lastnodetype.startswith('BUILD_LIST'):
                    self.write('['); endchar = ']'
                elif lastnodetype.startswith('BUILD_TUPLE'):
                    # Tuples can appear places that can NOT
                    # have parenthesis around them, like array
                    # subscripts. We check for that by seeing
                    # if a tuple item is some sort of slice.
                    no_parens = False
                    for n in node:
                        if n == 'expr' and n[0].kind.startswith('build_slice'):
                            no_parens = True
                            break
                        pass
                    if no_parens:
                        endchar = ''
                    else:
                        self.write('('); endchar = ')'
                        pass

                elif lastnodetype.startswith('BUILD_SET'):
                    self.write('{'); endchar = '}'
                elif lastnodetype.startswith('BUILD_MAP_UNPACK'):
                    self.write('{*'); endchar = '}'
                elif lastnodetype.startswith('ROT_TWO'):
                    self.write('('); endchar = ')'
                else:
                    raise TypeError('Internal Error: n_build_list expects list, tuple, set, or unpack')

                flat_elems = flatten_list(node)

                self.indent_more(INDENT_PER_LEVEL)
                sep = ''
                for elem in flat_elems:
                    if elem in ('ROT_THREE', 'EXTENDED_ARG'):
                        continue
                    assert elem == 'expr'
                    line_number = self.line_number
                    value = self.traverse(elem)
                    if elem[0] == 'tuple':
                        assert value[0] == '('
                        assert value[-1] == ')'
                        value = value[1:-1]
                        if value[-1] == ',':
                            # singleton tuple
                            value = value[:-1]
                    else:
                        value = '*' + value
                    if line_number != self.line_number:
                        sep += '\n' + self.indent + INDENT_PER_LEVEL[:-1]
                    else:
                        if sep != '': sep += ' '
                    if not last_was_star:
                        pass
                    else:
                        last_was_star = False
                    self.write(sep, value)
                    sep = ','
                if lastnode.attr == 1 and lastnodetype.startswith('BUILD_TUPLE'):
                    self.write(',')
                self.write(endchar)
                self.indent_less(INDENT_PER_LEVEL)

                self.prec = p
                self.prune()
                return

            self.n_tuple_unpack = n_list_unpack


        if version >= 3.6:
            ########################
            # Python 3.6+ Additions
            #######################

            # Value 100 is important; it is exactly
            # module/function precidence.
            PRECEDENCE['call_kw']     = 100
            PRECEDENCE['call_kw36']   = 100
            PRECEDENCE['call_ex']     = 100
            PRECEDENCE['call_ex_kw']  = 100
            PRECEDENCE['call_ex_kw2'] = 100
            PRECEDENCE['call_ex_kw3'] = 100
            PRECEDENCE['call_ex_kw4'] = 100
            PRECEDENCE['unmap_dict']  = 0

            TABLE_DIRECT.update({
                'tryfinally36':  ( '%|try:\n%+%c%-%|finally:\n%+%c%-\n\n',
                                   (1, 'returns'), 3 ),
                'fstring_expr':   ( "{%c%{conversion}}", 0),
                # FIXME: the below assumes the format strings
                # don't have ''' in them. Fix this properly
                'fstring_single': ( "f'''{%c%{conversion}}'''", 0),
                'fstring_multi':  ( "f'''%c'''", 0),
                'func_args36':    ( "%c(**", 0),
                'try_except36':   ( '%|try:\n%+%c%-%c\n\n', 1, 2 ),
                'except_return':  ( '%|except:\n%+%c%-', 3 ),
                'unpack_list':    ( '*%c', (0, 'list') ),
                'tryfinally_return_stmt':
                      ( '%|try:\n%+%c%-%|finally:\n%+%|return%-\n\n', 1 ),

                'call_ex' : (
                    '%c(%p)',
                    (0, 'expr'), (1, 100)),
                'call_ex_kw' : (
                    '%c(%p)',
                    (0, 'expr'), (2, 100)),

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
                if kwargs == 'dict':
                    self.call36_dict(kwargs)
                else:
                    self.write('**')
                    self.preorder(kwargs)
                self.write(')')
                self.prune()
            self.n_call_ex_kw3 = call_ex_kw3

            def call_ex_kw4(node):
                """Handle CALL_FUNCTION_EX {1 or 2} but without
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
                call_function_ex = node[-1]
                assert (call_function_ex == 'CALL_FUNCTION_EX_KW'
                        or (self.version >= 3.6 and call_function_ex == 'CALL_FUNCTION_EX'))
                # FIXME: decide if the below test be on kwargs == 'dict'
                if (call_function_ex.attr & 1 and
                    (not isinstance(kwargs, Token) and kwargs != 'attribute')
                    and not kwargs[0].kind.startswith('kvlist')):
                    self.call36_dict(kwargs)
                else:
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

                    length = len(l)
                    # FIXME: Parser-speed improved grammars will have BUILD_MAP
                    # at the end. So in the future when everything is
                    # complete, we can do an "assert" instead of "if".
                    if kv_node[-1].kind.startswith("BUILD_MAP"):
                        length -= 1

                    # Respect line breaks from source
                    while i < length:
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
                    self.write("**")
                    try:
                        self.default(node)
                    except GenericASTTraversalPruningException:
                        pass

                self.prec = p
                self.indent_less(INDENT_PER_LEVEL)
                return
            self.call36_dict = call36_dict


            FSTRING_CONVERSION_MAP = {1: '!s', 2: '!r', 3: '!a'}

            def n_except_suite_finalize(node):
                if node[1] == 'returns' and self.hide_internal:
                    # Process node[1] only.
                    # The code after "returns", e.g. node[3], is dead code.
                    # Adding it is wrong as it dedents and another
                    # exception handler "except_stmt" afterwards.
                    # Note it is also possible that the grammar is wrong here.
                    # and this should not be "except_stmt".
                    self.indent_more()
                    self.preorder(node[1])
                    self.indent_less()
                else:
                    self.default(node)
                self.prune()
            self.n_except_suite_finalize = n_except_suite_finalize

            def n_formatted_value(node):
                if node[0] == 'LOAD_CONST':
                    self.write(node[0].attr)
                    self.prune()
                else:
                    self.default(node)
            self.n_formatted_value = n_formatted_value

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

            def n_call_kw36(node):
                self.template_engine(("%c(", 0), node)
                keys = node[-2].attr
                num_kwargs = len(keys)
                num_posargs = len(node) - (num_kwargs + 2)
                n = len(node)
                assert n >= len(keys)+1, \
                  'not enough parameters keyword-tuple values'
                sep = ''

                line_number = self.line_number
                for i in range(1, num_posargs):
                    self.write(sep)
                    self.preorder(node[i])
                    if line_number != self.line_number:
                        sep = ",\n" + self.indent + "  "
                    else:
                        sep = ", "
                    line_number = self.line_number

                i = num_posargs
                j = 0
                # FIXME: adjust output for line breaks?
                while i < n-2:
                    self.write(sep)
                    self.write(keys[j] + '=')
                    self.preorder(node[i])
                    if line_number != self.line_number:
                        sep = ",\n" + self.indent + "  "
                    else:
                        sep = ", "
                    i += 1
                    j += 1
                self.write(')')
                self.prune()
                return
            self.n_call_kw36 = n_call_kw36

            def starred(node):
                l = len(node)
                assert l > 0
                pos_args = node[0]
                if pos_args == 'expr':
                    pos_args = pos_args[0]
                if pos_args == 'tuple':
                    build_tuple = pos_args[0]
                    if build_tuple.kind.startswith('BUILD_TUPLE'):
                        tuple_len = 0
                    else:
                        tuple_len = len(node) - 1
                    star_start = 1
                    template = '%C', (0, -1, ', ')
                    self.template_engine(template, pos_args)
                    if tuple_len == 0:
                        self.write("*()")
                        # That's it
                        self.prune()
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

            if version >= 3.7:
                PRECEDENCE['attribute37'] = 2
                TABLE_DIRECT.update({
                    'attribute37':  ( '%c.%[1]{pattr}', 0 ),
                    'async_forelse_stmt':  (
                        '%|async for %c in %c:\n%+%c%-%|else:\n%+%c%-\n\n',
                        7, 1, 17, (25, 'else_suite') ),
                    'async_for_stmt':  (
                        '%|async for %c in %c:\n%+%c%-%-\n\n',
                        7, 1, 17),
                    'compare_chained1a_37': ( ' %[3]{pattr.replace("-", " ")} %p %p',
                                             (0, 19),
                                             (-4, 19)),
                    'compare_chained1b_37': ( ' %[3]{pattr.replace("-", " ")} %p %p',
                                             (0, 19),
                                             (-4, 19)),
                    'compare_chained2a_37': ( '%[1]{pattr.replace("-", " ")} %p', (0, 19)),

                    'compare_chained2b_37': ( '%[1]{pattr.replace("-", " ")} %p', (0, 19)),

                    })
                pass
            pass # version >= 3.6
        pass # version >= 3.4
    return
