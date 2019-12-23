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

from uncompyle6.semantics.consts import TABLE_DIRECT

from xdis.code import iscode
from uncompyle6.scanner import Code
from uncompyle6.semantics.helper import gen_function_parens_adjust
from uncompyle6.semantics.make_function import make_function3_annotate
from uncompyle6.semantics.customize35 import customize_for_version35
from uncompyle6.semantics.customize36 import customize_for_version36
from uncompyle6.semantics.customize37 import customize_for_version37
from uncompyle6.semantics.customize38 import customize_for_version38


def customize_for_version3(self, version):
    TABLE_DIRECT.update(
        {
            "comp_for": (" for %c in %c", (2, "store"), (0, "expr")),
            "conditionalnot": (
                "%c if not %c else %c",
                (2, "expr"),
                (0, "expr"),
                (4, "expr"),
            ),
            "except_cond2": ("%|except %c as %c:\n", (1, "expr"), (5, "store")),
            "function_def_annotate": ("\n\n%|def %c%c\n", -1, 0),
            # When a generator is a single parameter of a function,
            # it doesn't need the surrounding parenethesis.
            "call_generator": ("%c%P", 0, (1, -1, ", ", 100)),
            "importmultiple": ("%|import %c%c\n", 2, 3),
            "import_cont": (", %c", 2),
            "kwarg": ("%[0]{attr}=%c", 1),
            "raise_stmt2": ("%|raise %c from %c\n", 0, 1),
            "store_locals": ("%|# inspect.currentframe().f_locals = __locals__\n",),
            "withstmt": ("%|with %c:\n%+%c%-", 0, 3),
            "withasstmt": ("%|with %c as %c:\n%+%c%-", 0, 2, 3),
        }
    )

    assert version >= 3.0

    def listcomp_closure3(node):
        """List comprehensions in Python 3 when handled as a closure.
        See if we can combine code.
        """
        p = self.prec
        self.prec = 27

        code = Code(node[1].attr, self.scanner, self.currentclass)
        ast = self.build_ast(code._tokens, code._customize)
        self.customize(code._customize)

        # skip over: sstmt, stmt, return, ret_expr
        # and other singleton derivations
        while len(ast) == 1 or (
            ast in ("sstmt", "return") and ast[-1] in ("RETURN_LAST", "RETURN_VALUE")
        ):
            self.prec = 100
            ast = ast[0]

        n = ast[1]

        # collections is the name of the expression(s) we are iterating over
        collections = [node[-3]]
        list_ifs = []

        if self.version == 3.0 and n != "list_iter":
            # FIXME 3.0 is a snowflake here. We need
            # special code for this. Not sure if this is totally
            # correct.
            stores = [ast[3]]
            assert ast[4] == "comp_iter"
            n = ast[4]
            # Find the list comprehension body. It is the inner-most
            # node that is not comp_.. .
            while n == "comp_iter":
                if n[0] == "comp_for":
                    n = n[0]
                    stores.append(n[2])
                    n = n[3]
                elif n[0] in ("comp_if", "comp_if_not"):
                    n = n[0]
                    # FIXME: just a guess
                    if n[0].kind == "expr":
                        list_ifs.append(n)
                    else:
                        list_ifs.append([1])
                    n = n[2]
                    pass
                else:
                    break
                pass

            # Skip over n[0] which is something like: _[1]
            self.preorder(n[1])

        else:
            assert n == "list_iter"
            stores = []
            # Find the list comprehension body. It is the inner-most
            # node that is not list_.. .
            while n == "list_iter":
                n = n[0]  # recurse one step
                if n == "list_for":
                    stores.append(n[2])
                    n = n[3]
                    if n[0] == "list_for":
                        # Dog-paddle down largely singleton reductions
                        # to find the collection (expr)
                        c = n[0][0]
                        if c == "expr":
                            c = c[0]
                        # FIXME: grammar is wonky here? Is this really an attribute?
                        if c == "attribute":
                            c = c[0]
                        collections.append(c)
                        pass
                elif n in ("list_if", "list_if_not"):
                    # FIXME: just a guess
                    if n[0].kind == "expr":
                        list_ifs.append(n)
                    else:
                        list_ifs.append([1])
                    n = n[2]
                    pass
                pass

            assert n == "lc_body", ast
            self.preorder(n[0])

        # FIXME: add indentation around "for"'s and "in"'s
        for i, store in enumerate(stores):
            self.write(" for ")
            self.preorder(store)
            self.write(" in ")
            self.preorder(collections[i])
            if i < len(list_ifs):
                self.preorder(list_ifs[i])
                pass
            pass
        self.prec = p
    self.listcomp_closure3 = listcomp_closure3

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
        if node == "classdefdeco2":
            if self.version >= 3.6:
                class_name = node[1][1].attr
            elif self.version <= 3.3:
                class_name = node[2][0].attr
            else:
                class_name = node[1][2].attr
            build_class = node
        else:
            build_class = node[0]
            if self.version >= 3.6:
                if build_class == "build_class_kw":
                    mkfunc = build_class[1]
                    assert mkfunc == "mkfunc"
                    subclass_info = build_class
                    if hasattr(mkfunc[0], "attr") and iscode(mkfunc[0].attr):
                        subclass_code = mkfunc[0].attr
                    else:
                        assert mkfunc[0] == "load_closure"
                        subclass_code = mkfunc[1].attr
                        assert iscode(subclass_code)
                if build_class[1][0] == "load_closure":
                    code_node = build_class[1][1]
                else:
                    code_node = build_class[1][0]
                class_name = code_node.attr.co_name
            else:
                class_name = node[1][0].attr
                build_class = node[0]

        assert "mkfunc" == build_class[1]
        mkfunc = build_class[1]
        if mkfunc[0] in ("kwargs", "no_kwargs"):
            if 3.0 <= self.version <= 3.2:
                for n in mkfunc:
                    if hasattr(n, "attr") and iscode(n.attr):
                        subclass_code = n.attr
                        break
                    elif n == "expr":
                        subclass_code = n[0].attr
                    pass
                pass
            else:
                for n in mkfunc:
                    if hasattr(n, "attr") and iscode(n.attr):
                        subclass_code = n.attr
                        break
                    pass
                pass
            if node == "classdefdeco2":
                subclass_info = node
            else:
                subclass_info = node[0]
        elif build_class[1][0] == "load_closure":
            # Python 3 with closures not functions
            load_closure = build_class[1]
            if hasattr(load_closure[-3], "attr"):
                # Python 3.3 classes with closures work like this.
                # Note have to test before 3.2 case because
                # index -2 also has an attr.
                subclass_code = load_closure[-3].attr
            elif hasattr(load_closure[-2], "attr"):
                # Python 3.2 works like this
                subclass_code = load_closure[-2].attr
            else:
                raise "Internal Error n_classdef: cannot find class body"
            if hasattr(build_class[3], "__len__"):
                if not subclass_info:
                    subclass_info = build_class[3]
            elif hasattr(build_class[2], "__len__"):
                subclass_info = build_class[2]
            else:
                raise "Internal Error n_classdef: cannot superclass name"
        elif self.version >= 3.6 and node == "classdefdeco2":
            subclass_info = node
            subclass_code = build_class[1][0].attr
        elif not subclass_info:
            if mkfunc[0] in ("no_kwargs", "kwargs"):
                subclass_code = mkfunc[1].attr
            else:
                subclass_code = mkfunc[0].attr
            if node == "classdefdeco2":
                subclass_info = node
            else:
                subclass_info = node[0]

        if node == "classdefdeco2":
            self.write("\n")
        else:
            self.write("\n\n")

        self.currentclass = str(class_name)
        self.write(self.indent, "class ", self.currentclass)

        self.print_super_classes3(subclass_info)
        self.println(":")

        # class body
        self.indent_more()
        self.build_class(subclass_code)
        self.indent_less()

        self.currentclass = cclass
        if len(self.param_stack) > 1:
            self.write("\n\n")
        else:
            self.write("\n\n\n")

        self.prune()

    self.n_classdef3 = n_classdef3

    if version == 3.0:
        # In Python 3.0 there is code to move from _[dd] into
        # the iteration variable. These rules we can ignore
        # since we pick up the iteration variable some other way and
        # we definitely don't include in the source  _[dd].
        TABLE_DIRECT.update({
            "ifstmt30":	( "%|if %c:\n%+%c%-",
                          (0, "testfalse_then"),
                          (1, "_ifstmts_jump30") ),
            "ifnotstmt30": ( "%|if not %c:\n%+%c%-",
                             (0, "testtrue_then"),
                             (1, "_ifstmts_jump30") ),
            "try_except30": ( "%|try:\n%+%c%-%c\n\n",
                              (1, "suite_stmts_opt"),
                              (4, "except_handler") ),

            })

        def n_comp_iter(node):
            if node[0] == "expr":
                n = node[0][0]
                if n == "LOAD_FAST" and n.pattr[0:2] == "_[":
                    self.prune()
                    pass
                pass
            # Not this special case, proceed as normal...
            self.default(node)

        self.n_comp_iter = n_comp_iter

    elif version == 3.3:
        # FIXME: perhaps this can be folded into the 3.4+ case?
        def n_yield_from(node):
            assert node[0] == "expr"
            if node[0][0] == "get_iter":
                # Skip over yield_from.expr.get_iter which adds an
                # extra iter(). Maybe we can do in tranformation phase instead?
                template = ("yield from %c", (0, "expr"))
                self.template_engine(template, node[0][0])
            else:
                template = ("yield from %c", (0, "attribute"))
                self.template_engine(template, node[0][0][0])
            self.prune()

        self.n_yield_from = n_yield_from

    if 3.2 <= version <= 3.4:

        def n_call(node):

            mapping = self._get_mapping(node)
            key = node
            for i in mapping[1:]:
                key = key[i]
                pass
            if key.kind.startswith("CALL_FUNCTION_VAR_KW"):
                # We may want to fill this in...
                # But it is distinct from CALL_FUNCTION_VAR below
                pass
            elif key.kind.startswith("CALL_FUNCTION_VAR"):
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
                        template = ("%c(*%c, %C)", 0, -2, (1, kwargs + 1, ", "))
                    else:
                        template = (
                            "%c(%C, *%c, %C)",
                            0,
                            (1, nargs + 1, ", "),
                            -2,
                            (-2 - kwargs, -2, ", "),
                        )
                    self.template_engine(template, node)
                    self.prune()
            else:
                gen_function_parens_adjust(key, node)
            self.default(node)

        self.n_call = n_call
    elif version < 3.2:

        def n_call(node):
            mapping = self._get_mapping(node)
            key = node
            for i in mapping[1:]:
                key = key[i]
                pass
            gen_function_parens_adjust(key, node)
            self.default(node)

        self.n_call = n_call

    def n_mkfunc_annotate(node):

        # Handling EXTENDED_ARG before MAKE_FUNCTION ...
        if node[-2] == "EXTENDED_ARG":
            i = -1
        else:
            i = 0

        if self.version <= 3.2:
            code = node[-2 + i]
        elif self.version >= 3.3 or node[-2] == "kwargs":
            # LOAD_CONST code object ..
            # LOAD_CONST        'x0'  if >= 3.3
            # EXTENDED_ARG
            # MAKE_FUNCTION ..
            code = node[-3 + i]
        elif node[-3] == "expr":
            code = node[-3][0]
        else:
            # LOAD_CONST code object ..
            # MAKE_FUNCTION ..
            code = node[-3]

        self.indent_more()
        for annotate_last in range(len(node) - 1, -1, -1):
            if node[annotate_last] == "annotate_tuple":
                break

        # FIXME: the real situation is that when derived from
        # function_def_annotate we the name has been filled in.
        # But when derived from funcdefdeco it hasn't Would like a better
        # way to distinquish.
        if self.f.getvalue()[-4:] == "def ":
            self.write(code.attr.co_name)

        # FIXME: handle and pass full annotate args
        make_function3_annotate(
            self, node, is_lambda=False, code_node=code, annotate_last=annotate_last
        )

        if len(self.param_stack) > 1:
            self.write("\n\n")
        else:
            self.write("\n\n\n")
        self.indent_less()
        self.prune()  # stop recursing

    self.n_mkfunc_annotate = n_mkfunc_annotate

    TABLE_DIRECT.update(
        {
            "tryelsestmtl3": (
                "%|try:\n%+%c%-%c%|else:\n%+%c%-",
                (1, "suite_stmts_opt"),
                (3, "except_handler"),
                (5, "else_suitel"),
            ),
            "LOAD_CLASSDEREF": ("%{pattr}",),
        }
    )
    if version >= 3.4:
        #######################
        # Python 3.4+ Changes #
        #######################
        TABLE_DIRECT.update(
            {
                "LOAD_CLASSDEREF": ("%{pattr}",),
                "yield_from": ("yield from %c", (0, "expr")),
            }
        )
        if version >= 3.5:
            customize_for_version35(self, version)
            if version >= 3.6:
                customize_for_version36(self, version)
                if version >= 3.7:
                    customize_for_version37(self, version)
                    if version >= 3.8:
                        customize_for_version38(self, version)
                        pass  # version >= 3.8
                    pass  # 3.7
                pass  # 3.6
            pass  # 3.5
        pass  # 3.4
    return
