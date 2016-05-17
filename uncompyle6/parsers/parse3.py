#  Copyright (c) 1999 John Aycock
#  Copyright (c) 2000-2002 by hartmut Goebel <h.goebel@crazy-compilers.com>
#  Copyright (c) 2005 by Dan Pascu <dan@windowmaker.org>
#  Copyright (c) 2015, 2016 Rocky Bernstein
#
#  See LICENSE for license
"""
A spark grammar for Python 3.x.

However instead of terminal symbols being the usual ASCII text,
e.g. 5, myvariable, "for", etc.  they are CPython Bytecode tokens,
e.g. "LOAD_CONST 5", "STORE NAME myvariable", "SETUP_LOOP", etc.

If we succeed in creating a parse tree, then we have a Python program
that a later phase can tern into a sequence of ASCII text.
"""

from __future__ import print_function

from uncompyle6.parser import PythonParser, PythonParserSingle, nop_func
from uncompyle6.parsers.astnode import AST
from spark_parser import DEFAULT_DEBUG as PARSER_DEFAULT_DEBUG
from uncompyle6 import PYTHON3

class Python3Parser(PythonParser):

    def __init__(self, debug_parser=PARSER_DEFAULT_DEBUG):
        self.added_rules = set()
        if PYTHON3:
            super().__init__(AST, 'stmts', debug=debug_parser)
        else:
            super(Python3Parser, self).__init__(AST, 'stmts', debug=debug_parser)
        self.new_rules = set()

    def add_unique_rule(self, rule, opname, count, customize):
        """Add rule to grammar, but only if it hasn't been added previously
        """
        if rule not in self.new_rules:
            # print("XXX ", rule) # debug
            self.new_rules.add(rule)
            self.addRule(rule, nop_func)
            customize[opname] = count
            pass
        return

    def p_list_comprehension3(self, args):
        """
        # Python3 scanner adds LOAD_LISTCOMP. Python3 does list comprehension like
        # other comprehensions (set, dictionary).

        # listcomp is a custom Python3 rule
        expr ::= listcomp

        list_for ::= expr FOR_ITER designator list_iter JUMP_BACK

        # See also common Python p_list_comprehension
        """

    def p_setcomp3(self, args):
        """
        # This is different in Python 2 - should it be?
        comp_for ::= expr _for designator comp_iter JUMP_ABSOLUTE

        # See also common Python p_setcomp
        """

    def p_grammar(self, args):
        '''
        sstmt ::= stmt
        sstmt ::= ifelsestmtr
        sstmt ::= return_stmt RETURN_LAST

        stmts_opt ::= stmts
        stmts_opt ::= passstmt
        passstmt ::=

        _stmts ::= _stmts stmt
        _stmts ::= stmt

        # statements with continue
        c_stmts ::= _stmts
        c_stmts ::= _stmts lastc_stmt
        c_stmts ::= lastc_stmt
        c_stmts ::= continue_stmts

        lastc_stmt ::= iflaststmt
        lastc_stmt ::= whileelselaststmt
        lastc_stmt ::= forelselaststmt
        lastc_stmt ::= ifelsestmtr
        lastc_stmt ::= ifelsestmtc
        lastc_stmt ::= tryelsestmtc

        c_stmts_opt ::= c_stmts
        c_stmts_opt ::= passstmt

        l_stmts ::= _stmts
        l_stmts ::= return_stmts
        l_stmts ::= continue_stmts
        l_stmts ::= _stmts lastl_stmt
        l_stmts ::= lastl_stmt

        lastl_stmt ::= iflaststmtl
        lastl_stmt ::= ifelsestmtl
        lastl_stmt ::= forelselaststmtl
        lastl_stmt ::= tryelsestmtl

        l_stmts_opt ::= l_stmts
        l_stmts_opt ::= passstmt

        suite_stmts ::= _stmts
        suite_stmts ::= return_stmts
        suite_stmts ::= continue_stmts

        suite_stmts_opt ::= suite_stmts
        suite_stmts_opt ::= passstmt

        else_suite ::= suite_stmts
        else_suitel ::= l_stmts
        else_suitec ::= c_stmts
        else_suitec ::= return_stmts

        designList ::= designator designator
        designList ::= designator DUP_TOP designList

        designator ::= STORE_FAST
        designator ::= STORE_NAME
        designator ::= STORE_GLOBAL
        designator ::= STORE_DEREF
        designator ::= expr STORE_ATTR
        designator ::= expr STORE_SLICE+0
        designator ::= expr expr STORE_SLICE+1
        designator ::= expr expr STORE_SLICE+2
        designator ::= expr expr expr STORE_SLICE+3
        designator ::= store_subscr
        store_subscr ::= expr expr STORE_SUBSCR
        designator ::= unpack
        designator ::= unpack_list

        stmt ::= classdef
        stmt ::= call_stmt

        stmt ::= return_stmt
        return_stmt ::= ret_expr RETURN_VALUE
        return_stmts ::= return_stmt
        return_stmts ::= _stmts return_stmt

        return_if_stmts ::= return_if_stmt come_from_opt
        return_if_stmts ::= _stmts return_if_stmt
        return_if_stmt ::= ret_expr RETURN_VALUE

        stmt ::= break_stmt
        break_stmt ::= BREAK_LOOP

        stmt ::= continue_stmt
        continue_stmt ::= CONTINUE
        continue_stmt ::= CONTINUE_LOOP
        continue_stmts ::= _stmts lastl_stmt continue_stmt
        continue_stmts ::= lastl_stmt continue_stmt
        continue_stmts ::= continue_stmt

        stmt ::= raise_stmt0
        stmt ::= raise_stmt1
        stmt ::= raise_stmt2
        stmt ::= raise_stmt3

        raise_stmt0 ::= RAISE_VARARGS_0
        raise_stmt1 ::= expr RAISE_VARARGS_1
        raise_stmt2 ::= expr expr RAISE_VARARGS_2
        raise_stmt3 ::= expr expr expr RAISE_VARARGS_3

        stmt ::= exec_stmt
        exec_stmt ::= expr exprlist DUP_TOP EXEC_STMT
        exec_stmt ::= expr exprlist EXEC_STMT

        stmt ::= assert
        stmt ::= assert2
        stmt ::= ifstmt
        stmt ::= ifelsestmt

        stmt ::= whilestmt
        stmt ::= whilenotstmt
        stmt ::= while1stmt
        stmt ::= whileelsestmt
        stmt ::= while1elsestmt
        stmt ::= forstmt
        stmt ::= forelsestmt
        stmt ::= trystmt
        stmt ::= tryelsestmt
        stmt ::= tryfinallystmt
        stmt ::= withstmt
        stmt ::= withasstmt

        stmt ::= del_stmt
        del_stmt ::= DELETE_FAST
        del_stmt ::= DELETE_NAME
        del_stmt ::= DELETE_GLOBAL
        del_stmt ::= expr DELETE_SLICE+0
        del_stmt ::= expr expr DELETE_SLICE+1
        del_stmt ::= expr expr DELETE_SLICE+2
        del_stmt ::= expr expr expr DELETE_SLICE+3
        del_stmt ::= delete_subscr
        delete_subscr ::= expr expr DELETE_SUBSCR
        del_stmt ::= expr DELETE_ATTR

        kwarg   ::= LOAD_CONST expr
        kwargs  ::= kwargs kwarg
        kwargs  ::=

        classdef ::= build_class designator
        # Python3 introduced LOAD_BUILD_CLASS
        # the definition of build_class is a custom rule

        stmt ::= classdefdeco
        classdefdeco ::= classdefdeco1 designator
        classdefdeco1 ::= expr classdefdeco1 CALL_FUNCTION_1
        classdefdeco1 ::= expr classdefdeco2 CALL_FUNCTION_1
        classdefdeco2 ::= LOAD_CONST expr mkfunc CALL_FUNCTION_0 BUILD_CLASS

        _jump ::= JUMP_ABSOLUTE
        _jump ::= JUMP_FORWARD
        _jump ::= JUMP_BACK

        jmp_false   ::= POP_JUMP_IF_FALSE
        jmp_false   ::= JUMP_IF_FALSE
        jmp_true    ::= POP_JUMP_IF_TRUE
        jmp_true    ::= JUMP_IF_TRUE

        assert ::= assert_expr jmp_true LOAD_ASSERT RAISE_VARARGS_1
        assert2 ::= assert_expr jmp_true LOAD_ASSERT expr CALL_FUNCTION_1 RAISE_VARARGS_1
        assert2 ::= assert_expr jmp_true LOAD_ASSERT expr RAISE_VARARGS_2

        assert_expr ::= expr
        assert_expr ::= assert_expr_or
        assert_expr ::= assert_expr_and
        assert_expr_or ::= assert_expr jmp_true expr
        assert_expr_and ::= assert_expr jmp_false expr

        ifstmt ::= testexpr _ifstmts_jump

        testexpr ::= testfalse
        testexpr ::= testtrue
        testfalse ::= expr jmp_false
        testtrue ::= expr jmp_true

        _ifstmts_jump ::= return_if_stmts
        _ifstmts_jump ::= c_stmts_opt JUMP_FORWARD COME_FROM

        iflaststmt ::= testexpr c_stmts_opt JUMP_ABSOLUTE

        iflaststmtl ::= testexpr c_stmts_opt JUMP_BACK

        ifelsestmt ::= testexpr c_stmts_opt JUMP_FORWARD else_suite COME_FROM

        ifelsestmtc ::= testexpr c_stmts_opt JUMP_ABSOLUTE else_suitec

        ifelsestmtr ::= testexpr return_if_stmts return_stmts

        ifelsestmtl ::= testexpr c_stmts_opt JUMP_BACK else_suitel


        # FIXME: this feels like a hack. Is it just 1 or two
        # COME_FROMs?  the parsed tree for this and even with just the
        # one COME_FROM for Python 2.7 seems to associate the
        # COME_FROM targets from the wrong places

        trystmt        ::= SETUP_EXCEPT suite_stmts_opt POP_BLOCK
                           try_middle _come_from

        # this is nested inside a trystmt
        tryfinallystmt ::= SETUP_FINALLY suite_stmts_opt
                           POP_BLOCK LOAD_CONST
                           COME_FROM suite_stmts_opt END_FINALLY

        tryelsestmt    ::= SETUP_EXCEPT suite_stmts_opt POP_BLOCK
                           try_middle else_suite COME_FROM

        tryelsestmtc ::= SETUP_EXCEPT suite_stmts_opt POP_BLOCK
                         try_middle else_suitec COME_FROM

        tryelsestmtl ::= SETUP_EXCEPT suite_stmts_opt POP_BLOCK
                         try_middle else_suitel COME_FROM

        try_middle ::= jmp_abs COME_FROM except_stmts
                       END_FINALLY
        try_middle ::= JUMP_FORWARD COME_FROM except_stmts
                       END_FINALLY COME_FROM

        except_stmts ::= except_stmts except_stmt
        except_stmts ::= except_stmt

        except_stmt ::= except_cond1 except_suite
        except_stmt ::= except_cond2 except_suite
        except_stmt ::= except_cond2 except_suite_finalize
        except_stmt ::= except
        except_stmt ::= except_pop_except

        # Python3 introduced POP_EXCEPT
        except_suite ::= c_stmts_opt POP_EXCEPT JUMP_FORWARD
        except_suite ::= c_stmts_opt POP_EXCEPT jmp_abs

        # This is used in Python 3 in
        # "except ... as e" to remove 'e' after the c_stmts_opt finishes
        except_suite_finalize ::= SETUP_FINALLY c_stmts_opt except_var_finalize
                                  END_FINALLY _jump

        except_var_finalize ::= POP_BLOCK POP_EXCEPT LOAD_CONST COME_FROM LOAD_CONST
                                designator del_stmt

        except_suite ::= return_stmts

        except_cond1 ::= DUP_TOP expr COMPARE_OP
                jmp_false POP_TOP POP_TOP POP_TOP

        except_cond2 ::= DUP_TOP expr COMPARE_OP
                jmp_false POP_TOP designator POP_TOP

        except  ::=  POP_TOP POP_TOP POP_TOP c_stmts_opt POP_EXCEPT JUMP_FORWARD
        except  ::=  POP_TOP POP_TOP POP_TOP return_stmts

        except_pop_except  ::=  POP_TOP POP_TOP POP_TOP POP_EXCEPT c_stmts_opt JUMP_FORWARD
        except_pop_except  ::=  POP_TOP POP_TOP POP_TOP POP_EXCEPT c_stmts_opt jmp_abs

        jmp_abs ::= JUMP_ABSOLUTE
        jmp_abs ::= JUMP_BACK

        withstmt ::= expr SETUP_WITH POP_TOP suite_stmts_opt
                POP_BLOCK LOAD_CONST COME_FROM
                WITH_CLEANUP END_FINALLY

        withasstmt ::= expr SETUP_WITH designator suite_stmts_opt
                POP_BLOCK LOAD_CONST COME_FROM
                WITH_CLEANUP END_FINALLY

        '''

    def p_misc(self, args):
        """
        _jump ::= NOP
        try_middle ::= JUMP_FORWARD COME_FROM except_stmts END_FINALLY NOP COME_FROM
        """

    def p_stmt3(self, args):
        """
        stmt ::= LOAD_CLOSURE RETURN_VALUE RETURN_LAST
        stmt ::= whileTruestmt
        ifelsestmt ::= testexpr c_stmts_opt JUMP_FORWARD else_suite _come_from

        forstmt ::= SETUP_LOOP expr _for designator for_block POP_BLOCK NOP _come_from
        whileTruestmt ::= SETUP_LOOP l_stmts_opt JUMP_BACK POP_BLOCK _come_from
        whileTruestmt ::= SETUP_LOOP l_stmts_opt JUMP_BACK POP_BLOCK NOP _come_from

        # Python < 3.5 no POP BLOCK
        whileTruestmt ::= SETUP_LOOP l_stmts_opt JUMP_BACK _come_from
        whileTruestmt ::= SETUP_LOOP l_stmts_opt JUMP_BACK NOP _come_from
        """

    def p_genexpr3(self, args):
        '''
        load_genexpr ::= LOAD_GENEXPR
        load_genexpr ::= BUILD_TUPLE_1 LOAD_GENEXPR LOAD_CONST

        # Is there something general going on here?
        genexpr ::= LOAD_GENEXPR LOAD_CONST MAKE_FUNCTION_0 expr GET_ITER CALL_FUNCTION_1
        genexpr ::= load_closure LOAD_GENEXPR LOAD_CONST MAKE_CLOSURE_0 expr GET_ITER CALL_FUNCTION_1
        '''

    def p_expr3(self, args):
        '''
        expr ::= LOAD_CLASSNAME
        # Python3 drops slice0..slice3

        # Python 3.3+ adds yield from
        expr ::= yield_from
        yield_from ::= expr expr YIELD_FROM

        # In Python 2, DUP_TOP_TWO is DUP_TOPX_2
        binary_subscr2 ::= expr expr DUP_TOP_TWO BINARY_SUBSCR
        '''

    @staticmethod
    def call_fn_name(token):
        """Customize CALL_FUNCTION to add the number of positional arguments"""
        return '%s_%i' % (token.type, token.attr)

    def custom_build_class_rule(self, opname, i, token, tokens, customize):
        '''
        # Should the first rule be somehow folded into the 2nd one?
        build_class ::= LOAD_BUILD_CLASS mkfunc
                        LOAD_CLASSNAME {expr}^n CALL_FUNCTION_n+2
                        LOAD_CONST CALL_FUNCTION_n
        build_class ::= LOAD_BUILD_CLASS mkfunc
                        expr
                        call_function
                        CALL_FUNCTION_3
        '''
        # FIXME: I bet this can be simplified
        # look for next MAKE_FUNCTION
        for i in range(i+1, len(tokens)):
            if tokens[i].type.startswith('MAKE_FUNCTION'):
                break
            elif tokens[i].type.startswith('MAKE_CLOSURE'):
                break
            pass
        assert i < len(tokens), "build_class needs to find MAKE_FUNCTION"
        assert tokens[i+1].type == 'LOAD_CONST', \
          "build_class expecting CONST after MAKE_FUNCTION"
        for i in range(i, len(tokens)):
            if tokens[i].type == 'CALL_FUNCTION':
                call_fn_tok = tokens[i]
                break
        assert call_fn_tok, "build_class custom rule needs to find CALL_FUNCTION"

        # customize build_class rule
        call_function = self.call_fn_name(call_fn_tok)
        args_pos = call_fn_tok.attr & 0xff
        args_kw = (call_fn_tok.attr >> 8) & 0xff
        rule = ("build_class ::= LOAD_BUILD_CLASS mkfunc %s"
                "%s" % (('expr ' * (args_pos - 1) + ('kwarg ' * args_kw)),
                        call_function))
        self.add_unique_rule(rule, opname, token.attr, customize)

        # Can the above build_class rule be folded into this rule?
        rule = ("build_class ::= LOAD_BUILD_CLASS mkfunc expr call_function "
                "CALL_FUNCTION_" + str(args_pos+1))
        self.add_unique_rule(rule, opname, token.attr, customize)
        return

    def custom_classfunc_rule(self, opname, token, customize):
        """
        call_function ::= expr {expr}^n CALL_FUNCTION_n
        call_function ::= expr {expr}^n CALL_FUNCTION_VAR_n POP_TOP
        call_function ::= expr {expr}^n CALL_FUNCTION_VAR_KW_n POP_TOP
        call_function ::= expr {expr}^n CALL_FUNCTION_KW_n POP_TOP
        """
        # Low byte indicates number of positional paramters,
        # high byte number of positional parameters
        args_pos = token.attr & 0xff
        args_kw = (token.attr >> 8) & 0xff
        nak = ( len(opname)-len('CALL_FUNCTION') ) // 3
        token.type = self.call_fn_name(token)
        rule = ('call_function ::= expr '
                + ('pos_arg ' * args_pos)
                + ('kwarg ' * args_kw)
                + 'expr ' * nak + token.type)
        self.add_unique_rule(rule, token.type, args_pos, customize)

    def add_custom_rules(self, tokens, customize):
        """
        Special handling for opcodes that take a variable number
        of arguments -- we add a new rule for each:

            Python 3.4+:
            listcomp ::= LOAD_LISTCOMP LOAD_CONST MAKE_FUNCTION_0 expr
                         GET_ITER CALL_FUNCTION_1
            listcomp ::= {expr}^n LOAD_LISTCOMP MAKE_CLOSURE
                         GET_ITER CALL_FUNCTION_1
            Python < 3.4
            listcomp ::= LOAD_LISTCOMP MAKE_FUNCTION_0 expr
                         GET_ITER CALL_FUNCTION_1


            setcomp ::= {expr}^n LOAD_SETCOMP MAKE_CLOSURE
                        GET_ITER CALL_FUNCTION_1

            dictcomp ::= LOAD_DICTCOMP MAKE_FUNCTION_0 expr
                         GET_ITER CALL_FUNCTION_1

            # build_class (see load_build_class)

            build_list  ::= {expr}^n BUILD_LIST_n
            build_list  ::= {expr}^n BUILD_TUPLE_n

            load_closure  ::= {LOAD_CLOSURE}^n BUILD_TUPLE_n

            unpack_list ::= UNPACK_LIST {expr}^n
            unpack      ::= UNPACK_TUPLE {expr}^n
            unpack      ::= UNPACK_SEQEUENCE {expr}^n

            mkfunc      ::= {pos_arg}^n LOAD_CONST MAKE_FUNCTION_n
            mklambda    ::= {pos_arg}^n LOAD_LAMBDA MAKE_FUNCTION_n
            mkfunc      ::= {pos_arg}^n load_closure LOAD_CONST MAKE_FUNCTION_n
            genexpr     ::= {pos_arg}^n LOAD_GENEXPR MAKE_FUNCTION_n

            listcomp ::= load_closure expr GET_ITER CALL_FUNCTION_1

            # call_function (see custom_classfunc_rule)
        """
        # from trepan.api import debug
        # debug(start_opts={'startup-profile': True})
        for i, token in enumerate(tokens):
            opname = token.type
            opname_base = opname[:opname.rfind('_')]

            if opname in ('CALL_FUNCTION', 'CALL_FUNCTION_VAR',
                          'CALL_FUNCTION_VAR_KW', 'CALL_FUNCTION_KW'):
                self.custom_classfunc_rule(opname, token, customize)
            elif opname == 'LOAD_LISTCOMP':
                if self.version >= 3.4:
                    rule = ("listcomp ::= LOAD_LISTCOMP LOAD_CONST MAKE_FUNCTION_0 expr "
                            "GET_ITER CALL_FUNCTION_1")
                else:
                    rule = ("listcomp ::= LOAD_LISTCOMP MAKE_FUNCTION_0 expr "
                            "GET_ITER CALL_FUNCTION_1")
                self.add_unique_rule(rule, opname, token.attr, customize)
            elif opname == 'LOAD_BUILD_CLASS':
                self.custom_build_class_rule(opname, i, token, tokens, customize)
            elif opname_base in ('BUILD_LIST', 'BUILD_TUPLE', 'BUILD_SET'):
                v = token.attr
                rule = ('build_list ::= ' + 'expr1024 ' * int(v//1024) +
                                        'expr32 ' * int((v//32)%32) + 'expr '*(v%32) + opname)
                self.add_unique_rule(rule, opname, token.attr, customize)
                if opname_base == 'BUILD_TUPLE':
                    rule = ('load_closure ::= %s%s' % (('LOAD_CLOSURE ' * v), opname))
                    self.add_unique_rule(rule, opname, token.attr, customize)

            elif opname_base == 'BUILD_MAP':
                kvlist_n = "kvlist_%s" % token.attr
                if self.version >= 3.5:
                    rule = kvlist_n + ' ::= ' + 'expr ' * (token.attr*2)
                    self.add_unique_rule(rule, opname, token.attr, customize)
                    rule = "mapexpr ::=  %s %s" % (kvlist_n, opname)
                else:
                    rule = kvlist_n + ' ::= ' + 'expr expr STORE_MAP ' * token.attr
                    self.add_unique_rule(rule, opname, token.attr, customize)
                    rule = "mapexpr ::=  %s %s" % (opname, kvlist_n)
                self.add_unique_rule(rule, opname, token.attr, customize)
            elif opname_base in ('UNPACK_TUPLE', 'UNPACK_SEQUENCE'):
                rule = 'unpack ::= ' + opname + ' designator' * token.attr
                self.add_unique_rule(rule, opname, token.attr, customize)
            elif opname_base == 'UNPACK_LIST':
                rule = 'unpack_list ::= ' + opname + ' designator' * token.attr
            elif opname_base.startswith('MAKE_FUNCTION'):
                args_pos, args_kw, annotate_args  = token.attr
                rule = ('mklambda ::= %sLOAD_LAMBDA LOAD_CONST %s' %
                        ('pos_arg '* args_pos, opname))
                self.add_unique_rule(rule, opname, token.attr, customize)
                if self.version > 3.2:
                    rule = ('mkfunc ::= %skwargs %s %s' %
                            ('pos_arg ' * args_pos,
                                 'LOAD_CONST ' * 2,
                            opname))
                else:
                    rule = ('mkfunc ::= %sLOAD_CONST %s' %
                            ('pos_arg ' * args_pos, opname))
                self.add_unique_rule(rule, opname, token.attr, customize)
            elif opname.startswith('MAKE_CLOSURE'):
                self.add_unique_rule('mklambda ::= %sload_closure LOAD_LAMBDA LOAD_CONST %s' %
                                     ('pos_arg ' * token.attr, opname), opname, token.attr,
                                     customize)
                self.add_unique_rule('genexpr ::= %sload_closure '
                                     'load_genexpr %s '
                                     'expr GET_ITER CALL_FUNCTION_1' %
                                     ('pos_arg ' * token.attr, opname),
                                     opname, token.attr, customize)
                if self.version >= 3.4:
                    self.add_unique_rule('listcomp ::= %sload_closure '
                                         'LOAD_LISTCOMP LOAD_CONST %s expr '
                                         'GET_ITER CALL_FUNCTION_1' %
                                         ('expr ' * token.attr, opname),
                                         opname, token.attr, customize)
                else:
                    self.add_unique_rule('listcomp ::= %sload_closure '
                                         'LOAD_LISTCOMP %s expr '
                                         'GET_ITER CALL_FUNCTION_1' %
                                        ('expr ' * token.attr, opname),
                                        opname, token.attr, customize)

                self.add_unique_rule('setcomp ::= %sload_closure LOAD_SETCOMP %s expr '
                                     'GET_ITER CALL_FUNCTION_1' %
                                     ('expr ' * token.attr, opname),
                                     opname, token.attr, customize)
                self.add_unique_rule('dictcomp ::= %sload_closure LOAD_DICTCOMP %s '
                                     'expr GET_ITER CALL_FUNCTION_1' %
                                     ('pos_arg '* token.attr, opname),
                                     opname, token.attr, customize)

                rule = ('mkfunc ::= %s load_closure LOAD_CONST %s'
                        % ('expr ' * token.attr, opname))

                # Python 3.5+ instead of above?
                rule = ('mkfunc ::= %s load_closure LOAD_CONST LOAD_CONST %s'
                        % ('expr ' * token.attr, opname))

                self.add_unique_rule(rule, opname, token.attr, customize)
                rule = ('mkfunc ::= %s load_closure load_genexpr %s'
                        % ('pos_arg ' * token.attr, opname))
                self.add_unique_rule(rule, opname, token.attr, customize)
                rule = ('mkfunc ::= %s load_closure LOAD_CONST %s'
                        % ('expr ' * token.attr, opname))
                self.add_unique_rule(rule, opname, token.attr, customize)
        return


class Python32Parser(Python3Parser):
    def p_32(self, args):
        """
        # Store locals is only in Python 3.2 and 3.3
        designator ::= STORE_LOCALS
        """

class Python33Parser(Python3Parser):
    def p_33(self, args):
        """
        # Store locals is only in Python 3.2 and 3.3
        designator ::= STORE_LOCALS
        """

class Python34Parser(Python3Parser):
    def p_34(self, args):
        """
        _ifstmts_jump ::= c_stmts_opt JUMP_FORWARD _come_from
        """

class Python35onParser(Python3Parser):
    def p_35on(self, args):
        """
        # Python 3.5+ has WITH_CLEANUP_START/FINISH
        withstmt ::= expr SETUP_WITH with_setup suite_stmts_opt
                     POP_BLOCK LOAD_CONST COME_FROM
                     WITH_CLEANUP_START WITH_CLEANUP_FINISH END_FINALLY

        withasstmt ::= expr SETUP_WITH designator suite_stmts_opt
                POP_BLOCK LOAD_CONST COME_FROM
                WITH_CLEANUP_START WITH_CLEANUP_FINISH END_FINALLY

        # Python 3.5 has more loop optimization that removes
        # JUMP_FORWARD in some cases, and hence we also don't
        # see COME_FROM
        _ifstmts_jump ::= c_stmts_opt
        """

class Python3ParserSingle(Python3Parser, PythonParserSingle):
    pass


class Python32ParserSingle(Python32Parser, PythonParserSingle):
    pass


class Python33ParserSingle(Python33Parser, PythonParserSingle):
    pass

class Python34ParserSingle(Python34Parser, PythonParserSingle):
    pass


class Python35onParserSingle(Python35onParser, PythonParserSingle):
    pass
