#  Copyright (c) 2015, 2016 Rocky Bernstein
#  Copyright (c) 2005 by Dan Pascu <dan@windowmaker.org>
#  Copyright (c) 2000-2002 by hartmut Goebel <h.goebel@crazy-compilers.com>
#  Copyright (c) 1999 John Aycock
#
#  See LICENSE for license
"""
A spark grammar for Python 3.x.

However instead of terminal symbols being the usual ASCII text,
e.g. 5, myvariable, "for", etc.  they are CPython Bytecode tokens,
e.g. "LOAD_CONST 5", "STORE NAME myvariable", "SETUP_LOOP", etc.

If we succeed in creating a parse tree, then we have a Python program
that a later phase can turn into a sequence of ASCII text.
"""

from __future__ import print_function

from uncompyle6.parser import PythonParser, PythonParserSingle
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

    def p_list_comprehension3(self, args):
        """
        # Python3 scanner adds LOAD_LISTCOMP. Python3 does list comprehension like
        # other comprehensions (set, dictionary).

        # listcomp is a custom Python3 rule
        expr ::= listcomp

        # Our "continue" heuristic -  in two successive JUMP_BACKS, the first
        # one may be a continue - sometimes classifies a JUMP_BACK
        # as a CONTINUE. The two are kind of the same in a comprehension.

        comp_for ::= expr _for designator comp_iter CONTINUE

        list_for ::= expr FOR_ITER designator list_iter jb_or_c

        jb_or_c ::= JUMP_BACK
        jb_or_c ::= CONTINUE

        # See also common Python p_list_comprehension
        """

    def p_dictcomp3(self, args):
        """"
        dictcomp ::= LOAD_DICTCOMP LOAD_CONST MAKE_FUNCTION_0 expr GET_ITER CALL_FUNCTION_1
        """

    def p_grammar(self, args):
        '''
        sstmt ::= stmt
        sstmt ::= ifelsestmtr
        sstmt ::= return_stmt RETURN_LAST

        return_if_stmts ::= return_if_stmt come_from_opt
        return_if_stmts ::= _stmts return_if_stmt
        return_if_stmt ::= ret_expr RETURN_END_IF

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
        # Other definitions are in a custom rule
        build_class ::= LOAD_BUILD_CLASS mkfunc expr call_function CALL_FUNCTION_3

        stmt ::= classdefdeco
        classdefdeco ::= classdefdeco1 designator
        classdefdeco1 ::= expr classdefdeco1 CALL_FUNCTION_1
        classdefdeco1 ::= expr classdefdeco2 CALL_FUNCTION_1

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
                           try_middle else_suite come_froms

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

        ## FIXME: what's except_pop_except?
        except_stmt ::= except_pop_except

        # Python3 introduced POP_EXCEPT
        except_suite ::= c_stmts_opt POP_EXCEPT jump_except
        jump_except ::= JUMP_ABSOLUTE
        jump_except ::= JUMP_BACK
        jump_except ::= JUMP_FORWARD
        jump_except ::= CONTINUE

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

        except  ::=  POP_TOP POP_TOP POP_TOP c_stmts_opt POP_EXCEPT _jump
        except  ::=  POP_TOP POP_TOP POP_TOP return_stmts

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
        try_middle ::= JUMP_FORWARD COME_FROM except_stmts END_FINALLY NOP COME_FROM
        """

    def p_jump3(self, args):
        """
        come_froms ::= come_froms COME_FROM
        come_froms ::= COME_FROM
        jmp_false ::= POP_JUMP_IF_FALSE
        jmp_true  ::= POP_JUMP_IF_TRUE
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
        while1stmt ::= SETUP_LOOP l_stmts _come_from JUMP_BACK _come_from
        """

    def p_genexpr3(self, args):
        '''
        load_genexpr ::= LOAD_GENEXPR
        load_genexpr ::= BUILD_TUPLE_1 LOAD_GENEXPR LOAD_CONST

        # Is there something general going on here?
        dictcomp ::= load_closure LOAD_DICTCOMP LOAD_CONST MAKE_CLOSURE_0 expr GET_ITER CALL_FUNCTION_1
        '''

    def p_expr3(self, args):
        '''
        expr ::= LOAD_CLASSNAME
        expr ::= LOAD_ASSERT

        # Python 3.4+
        expr ::= LOAD_CLASSDEREF

        # Python3 drops slice0..slice3

        # In Python 2, DUP_TOP_TWO is DUP_TOPX_2
        binary_subscr2 ::= expr expr DUP_TOP_TWO BINARY_SUBSCR
        '''

    def p_misc3(self, args):
        '''
        for_block ::= l_stmts
        iflaststmtl ::= testexpr c_stmts_opt
        iflaststmt    ::= testexpr c_stmts_opt34
        c_stmts_opt34 ::= JUMP_BACK JUMP_ABSOLUTE c_stmts_opt
        '''

    @staticmethod
    def call_fn_name(token):
        """Customize CALL_FUNCTION to add the number of positional arguments"""
        return '%s_%i' % (token.type, token.attr)

    def custom_build_class_rule(self, opname, i, token, tokens, customize):
        '''
        # Should the first rule be somehow folded into the 2nd one?
        build_class ::= LOAD_BUILD_CLASS mkfunc
                        LOAD_CLASSNAME {expr}^n-1 CALL_FUNCTION_n
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
        assert i < len(tokens), "build_class needs to find MAKE_FUNCTION or MAKE_CLOSURE"
        assert tokens[i+1].type == 'LOAD_CONST', \
          "build_class expecting CONST after MAKE_FUNCTION/MAKE_CLOSURE"
        for i in range(i, len(tokens)):
            if tokens[i].type == 'CALL_FUNCTION':
                call_fn_tok = tokens[i]
                break
        assert call_fn_tok, "build_class custom rule needs to find CALL_FUNCTION"

        # customize build_class rule
        # FIXME: What's the deal with the two rules? Different Python versions?
        # Different situations? Note that the above rule is based on the CALL_FUNCTION
        # token found, while this one doesn't.
        call_function = self.call_fn_name(call_fn_tok)
        args_pos = call_fn_tok.attr & 0xff
        args_kw = (call_fn_tok.attr >> 8) & 0xff
        rule = ("build_class ::= LOAD_BUILD_CLASS mkfunc %s"
                "%s" % (('expr ' * (args_pos - 1) + ('kwarg ' * args_kw)),
                        call_function))
        self.add_unique_rule(rule, opname, token.attr, customize)
        return

    def custom_classfunc_rule(self, opname, token, customize):
        """
        call_function ::= expr {expr}^n CALL_FUNCTION_n
        call_function ::= expr {expr}^n CALL_FUNCTION_VAR_n POP_TOP
        call_function ::= expr {expr}^n CALL_FUNCTION_VAR_KW_n POP_TOP
        call_function ::= expr {expr}^n CALL_FUNCTION_KW_n POP_TOP

        classdefdeco2 ::= LOAD_BUILD_CLASS mkfunc {expr}^n-1 CALL_FUNCTION_n
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
        rule = ('classdefdeco2 ::= LOAD_BUILD_CLASS mkfunc %s%s_%d'
                %  (('expr ' * (args_pos-1)), opname, args_pos))
        self.add_unique_rule(rule, token.type, args_pos, customize)

    def add_make_function_rule(self, rule, opname, attr, customize):
        """Python 3.3 added a an addtional LOAD_CONST before MAKE_FUNCTION and
        this has an effect on many rules.
        """
        new_rule = rule % (('LOAD_CONST ') * (1 if  self.version >= 3.3 else 0))
        self.add_unique_rule(new_rule, opname, attr, customize)

    def add_custom_rules(self, tokens, customize):
        """
        Special handling for opcodes that take a variable number
        of arguments -- we add a new rule for each:

            unpack_list ::= UNPACK_LIST_n {expr}^n
            unpack      ::= UNPACK_TUPLE_n {expr}^n
            unpack      ::= UNPACK_SEQEUENCE_n {expr}^n
            unpack_ex ::=   UNPACK_EX_b_a {expr}^(a+b)

            # build_class (see load_build_class)

            build_list  ::= {expr}^n BUILD_LIST_n
            build_list  ::= {expr}^n BUILD_TUPLE_n

            load_closure  ::= {LOAD_CLOSURE}^n BUILD_TUPLE_n
            # call_function (see custom_classfunc_rule)

            # ------------
            # Python <= 3.2 omits LOAD_CONST before MAKE_
            # Note: are the below specific instances of a more general case?
            # ------------

            # Is there something more general than this? adding pos_arg?
            # Is there something corresponding using MAKE_CLOSURE?
            dictcomp ::= LOAD_DICTCOMP [LOAD_CONST] MAKE_FUNCTION_0 expr
                           GET_ITER CALL_FUNCTION_1

            genexpr  ::= {pos_arg}^n load_genexpr [LOAD_CONST] MAKE_FUNCTION_n expr
                           GET_ITER CALL_FUNCTION_1
            genexpr  ::= {expr}^n load_closure LOAD_GENEXPR [LOAD_CONST]
                          MAKE_CLOSURE_n expr GET_ITER CALL_FUNCTION_1
            listcomp ::= {pos_arg}^n LOAD_LISTCOMP [LOAD_CONST] MAKE_CLOSURE_n expr
                           GET_ITER CALL_FUNCTION_1
            listcomp ::= {pos_arg}^n load_closure LOAD_LISTCOMP [LOAD_CONST]
                           MAKE_CLOSURE_n expr GET_ITER CALL_FUNCTION_1

            # Is there something more general than this? adding pos_arg?
            # Is there something corresponding using MAKE_CLOSURE?
            For example:
            # setcomp ::= {pos_arg}^n LOAD_SETCOMP [LOAD_CONST] MAKE_CLOSURE_n
                        GET_ITER CALL_FUNCTION_1

            setcomp  ::= LOAD_SETCOMP [LOAD_CONST] MAKE_FUNCTION_0 expr
                           GET_ITER CALL_FUNCTION_1
            setcomp  ::= {pos_arg}^n load_closure LOAD_SETCOMP [LOAD_CONST]
                           MAKE_CLOSURE_n expr GET_ITER CALL_FUNCTION_1

            mkfunc   ::= {pos_arg}^n load_closure [LOAD_CONST] MAKE_FUNCTION_n
            mkfunc   ::= {pos_arg}^n load_closure [LOAD_CONST] MAKE_CLOSURE_n
            mkfunc   ::= {pos_arg}^n [LOAD_CONST] MAKE_FUNCTION_n
            mklambda ::= {pos_arg}^n LOAD_LAMBDA [LOAD_CONST] MAKE_FUNCTION_n

        """
        for i, token in enumerate(tokens):
            opname = token.type
            opname_base = opname[:opname.rfind('_')]

            if opname in ('CALL_FUNCTION', 'CALL_FUNCTION_VAR',
                          'CALL_FUNCTION_VAR_KW', 'CALL_FUNCTION_KW'):
                self.custom_classfunc_rule(opname, token, customize)
            elif opname == 'LOAD_DICTCOMP':
                rule_pat = ("dictcomp ::= LOAD_DICTCOMP %sMAKE_FUNCTION_0 expr "
                            "GET_ITER CALL_FUNCTION_1")
                self.add_make_function_rule(rule_pat, opname, token.attr, customize)
            ## Custom rules which are handled now by the more generic rule in
            ## either MAKE_FUNCTION or MAKE_CLOSURE
            # elif opname == 'LOAD_GENEXPR':
            #     rule_pat = ("genexpr ::= LOAD_GENEXPR %sMAKE_FUNCTION_0 expr "
            #                 "GET_ITER CALL_FUNCTION_1")
            #     self.add_make_function_rule(rule_pat, opname, token.attr, customize)
            #     rule_pat = ("genexpr ::= load_closure LOAD_GENEXPR %sMAKE_CLOSURE_0 expr "
            #                 "GET_ITER CALL_FUNCTION_1")
            #     self.add_make_function_rule(rule_pat, opname, token.attr, customize)
            # elif opname == 'LOAD_LISTCOMP':
            #     rule_pat  = ("listcomp ::= LOAD_LISTCOMP %sMAKE_FUNCTION_0 expr "
            #                 "GET_ITER CALL_FUNCTION_1")
            #     self.add_make_function_rule(rule_pat, opname, token.attr, customize)
            elif opname == 'LOAD_SETCOMP':
                # Should this be generalized and put under MAKE_FUNCTION?
                rule_pat = ("setcomp ::= LOAD_SETCOMP %sMAKE_FUNCTION_0 expr "
                            "GET_ITER CALL_FUNCTION_1")
                self.add_make_function_rule(rule_pat, opname, token.attr, customize)
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
            elif opname_base in ('UNPACK_EX'):
                before_count, after_count = token.attr
                rule = 'unpack ::= ' + opname + ' designator' * (before_count + after_count + 1)
                self.add_unique_rule(rule, opname, token.attr, customize)
            elif opname_base in ('UNPACK_TUPLE', 'UNPACK_SEQUENCE'):
                rule = 'unpack ::= ' + opname + ' designator' * token.attr
                self.add_unique_rule(rule, opname, token.attr, customize)
            elif opname_base == 'UNPACK_LIST':
                rule = 'unpack_list ::= ' + opname + ' designator' * token.attr
            elif opname_base.startswith('MAKE_FUNCTION'):
                # DRY with MAKE_CLOSURE
                args_pos, args_kw, annotate_args  = token.attr

                rule_pat = ("genexpr ::= %sload_genexpr %%s%s expr "
                            "GET_ITER CALL_FUNCTION_1" % ('pos_arg '* args_pos, opname))
                self.add_make_function_rule(rule_pat, opname, token.attr, customize)
                rule_pat = ('mklambda ::= %sLOAD_LAMBDA %%s%s' % ('pos_arg '* args_pos, opname))
                self.add_make_function_rule(rule_pat, opname, token.attr, customize)
                rule_pat  = ("listcomp ::= %sLOAD_LISTCOMP %%s%s expr "
                             "GET_ITER CALL_FUNCTION_1" % ('expr ' * args_pos, opname))
                self.add_make_function_rule(rule_pat, opname, token.attr, customize)

                if self.version == 3.3:
                    # positional args after keyword args
                    rule = ('mkfunc ::= kwargs %s%s %s' %
                            ('pos_arg ' * args_pos, 'LOAD_CONST '*2,
                             opname))
                elif self.version > 3.3:
                    # positional args before keyword args
                    rule = ('mkfunc ::= %skwargs %s %s' %
                            ('pos_arg ' * args_pos, 'LOAD_CONST '*2,
                             opname))
                else:
                    rule = ('mkfunc ::= kwargs %sexpr %s' %
                            ('pos_arg ' * args_pos, opname))
                self.add_unique_rule(rule, opname, token.attr, customize)
            elif opname.startswith('MAKE_CLOSURE'):
                # DRY with MAKE_FUNCTION
                # Note: this probably doesn't handle kwargs proprerly
                args_pos, args_kw, annotate_args  = token.attr

                rule_pat = ("genexpr ::= %sload_closure load_genexpr %%s%s expr "
                            "GET_ITER CALL_FUNCTION_1" % ('pos_arg '* args_pos, opname))
                self.add_make_function_rule(rule_pat, opname, token.attr, customize)
                rule_pat = ('mklambda ::= %sload_closure LOAD_LAMBDA %%s%s' %
                            ('pos_arg '* args_pos, opname))
                self.add_make_function_rule(rule_pat, opname, token.attr, customize)
                rule_pat = ('listcomp ::= %sload_closure LOAD_LISTCOMP %%s%s expr '
                            'GET_ITER CALL_FUNCTION_1' % ('pos_arg ' * args_pos, opname))
                self.add_make_function_rule(rule_pat, opname, token.attr, customize)
                rule_pat = ('setcomp ::= %sload_closure LOAD_SETCOMP %%s%s expr '
                            'GET_ITER CALL_FUNCTION_1' % ('pos_arg ' * args_pos, opname))
                self.add_make_function_rule(rule_pat, opname, token.attr, customize)

                self.add_unique_rule('dictcomp ::= %sload_closure LOAD_DICTCOMP %s '
                                     'expr GET_ITER CALL_FUNCTION_1' %
                                     ('pos_arg '* args_pos, opname),
                                     opname, token.attr, customize)

                # FIXME: kwarg processing is missing here.
                # Note order of kwargs and pos args changed between 3.3-3.4
                if self.version <= 3.2:
                    rule = ('mkfunc ::= %sload_closure LOAD_CONST kwargs %s'
                            % ('expr ' * args_pos, opname))
                elif self.version >= 3.3:
                    rule = ('mkfunc ::= kwargs %sload_closure LOAD_CONST LOAD_CONST %s'
                            % ('expr ' * args_pos, opname))

                self.add_unique_rule(rule, opname, token.attr, customize)
                rule = ('mkfunc ::= %sload_closure load_genexpr %s'
                        % ('pos_arg ' * args_pos, opname))
                self.add_unique_rule(rule, opname, token.attr, customize)
                rule = ('mkfunc ::= %sload_closure LOAD_CONST %s'
                        % ('expr ' * args_pos, opname))
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

        # Python 3.3 adds yield from.
        expr ::= yield_from
        yield_from ::= expr expr YIELD_FROM
        """

class Python35onParser(Python3Parser):
    def p_35on(self, args):
        """
        # Python 3.5+ has WITH_CLEANUP_START/FINISH

        withstmt ::= expr SETUP_WITH exprlist suite_stmts_opt
                    POP_BLOCK LOAD_CONST COME_FROM
                    WITH_CLEANUP_START WITH_CLEANUP_FINISH END_FINALLY

        withstmt ::= expr SETUP_WITH POP_TOP suite_stmts_opt
                     POP_BLOCK LOAD_CONST COME_FROM
                     WITH_CLEANUP_START WITH_CLEANUP_FINISH END_FINALLY

        withasstmt ::= expr SETUP_WITH designator suite_stmts_opt
                POP_BLOCK LOAD_CONST COME_FROM
                WITH_CLEANUP_START WITH_CLEANUP_FINISH END_FINALLY


        # Python 3.5+_ does jump optimization that scanner3.py's detect
        # structure can't fully work out. So for now let's allow
        # RETURN_END_IF the same as RETURN_VAL
        return_stmt ::= ret_expr RETURN_END_IF

        # Python 3.3+ also has yield from. 3.5 does it
        # differently than 3.3, 3.4

        expr ::= yield_from
        yield_from ::= expr GET_YIELD_FROM_ITER LOAD_CONST YIELD_FROM

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

class Python35onParserSingle(Python35onParser, PythonParserSingle):
    pass

def info(args):
    # Check grammar
    # Should also add a way to dump grammar
    import sys
    p = Python3Parser()
    if len(args) > 0:
        arg = args[0]
        if arg == '3.5':
            p = Python35onParser()
        elif arg == '3.3':
            p = Python33Parser()
        elif arg == '3.2':
            p = Python32Parser()
    p.checkGrammar()


if __name__ == '__main__':
    import sys
    info(sys.argv)
