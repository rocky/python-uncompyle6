#  Copyright (c) 2017-2020, 2022-2024 Rocky Bernstein
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
"""
Python 3.7 grammar for the spark Earley-algorithm parser.
"""
from __future__ import print_function

from spark_parser import DEFAULT_DEBUG as PARSER_DEFAULT_DEBUG

from uncompyle6.parser import PythonParserSingle, nop_func
from uncompyle6.parsers.parse37base import Python37BaseParser
from uncompyle6.scanners.tok import Token


class Python37Parser(Python37BaseParser):
    def __init__(self, debug_parser=PARSER_DEFAULT_DEBUG):
        super(Python37Parser, self).__init__(debug_parser)
        self.customized = {}

    ###############################################
    #  Python 3.7 grammar rules
    ###############################################
    def p_start(self, args):
        """
        # The start or goal symbol
        stmts ::= sstmt+
        """

    def p_call_stmt(self, args):
        """
        # eval-mode compilation.  Single-mode interactive compilation
        # adds another rule.
        call_stmt ::= expr POP_TOP
        """

    def p_eval_mode(self, args):
        """
        # eval-mode compilation.  Single-mode interactive compilation
        # adds another rule.
        expr_stmt ::= expr POP_TOP
        """

    def p_stmt(self, args):
        """
        pass ::=

        _stmts ::= stmt+

        # statements with continue and break
        c_stmts ::= _stmts
        c_stmts ::= _stmts lastc_stmt
        c_stmts ::= lastc_stmt
        c_stmts ::= continues

        ending_return  ::= RETURN_VALUE RETURN_LAST
        ending_return  ::= RETURN_VALUE_LAMBDA LAMBDA_MARKER

        lastc_stmt ::= iflaststmt
        lastc_stmt ::= forelselaststmt
        lastc_stmt ::= ifelsestmtc

        # Statements in a loop
        lstmt              ::= stmt
        l_stmts            ::= lstmt+

        c_stmts_opt ::= c_stmts
        c_stmts_opt ::= pass

        # statements inside a loop
        l_stmts ::= _stmts
        l_stmts ::= returns
        l_stmts ::= continues
        l_stmts ::= _stmts lastl_stmt
        l_stmts ::= lastl_stmt

        lastl_stmt ::= iflaststmtl
        lastl_stmt ::= ifelsestmtl
        lastl_stmt ::= forelselaststmtl
        lastl_stmt ::= tryelsestmtl

        l_stmts_opt ::= l_stmts
        l_stmts_opt ::= pass

        suite_stmts ::= _stmts
        suite_stmts ::= returns
        suite_stmts ::= continues

        suite_stmts_opt ::= suite_stmts

        # passtmt is needed for semantic actions to add "pass"
        suite_stmts_opt ::= pass

        else_suite ::= suite_stmts
        else_suitel ::= l_stmts
        else_suitec ::= c_stmts
        else_suitec ::= returns

        else_suite_opt ::= else_suite
        else_suite_opt ::= pass

        stmt ::= classdef
        stmt ::= expr_stmt
        stmt ::= call_stmt

        stmt ::= ifstmt
        stmt ::= ifelsestmt

        stmt ::= whilestmt
        stmt ::= while1stmt
        stmt ::= whileelsestmt
        stmt ::= while1elsestmt
        stmt ::= for
        stmt ::= forelsestmt
        stmt ::= try_except
        stmt ::= tryelsestmt
        stmt ::= tryfinallystmt

        stmt   ::= delete
        delete ::= DELETE_FAST
        delete ::= DELETE_NAME
        delete ::= DELETE_GLOBAL

        stmt   ::= return
        return ::= return_expr RETURN_VALUE

        # "returns" nonterminal is a sequence of statements that ends in a
        # RETURN statement.
        # In later Python versions with jump optimization, this can cause JUMPs
        # that would normally appear to be omitted.

        returns ::= return
        returns ::= _stmts return

        stmt ::= genexpr_func
        genexpr_func ::= LOAD_ARG _come_froms FOR_ITER store comp_iter
                         _come_froms JUMP_BACK _come_froms
        """
        pass

    def p_expr(self, args):
        """
        expr ::= LOAD_CODE
        expr ::= LOAD_CONST
        expr ::= LOAD_DEREF
        expr ::= LOAD_FAST
        expr ::= LOAD_GLOBAL
        expr ::= LOAD_NAME
        expr ::= LOAD_STR
        expr ::= _lambda_body

        expr ::= and
        expr ::= attribute37

        expr ::= bin_op
        expr ::= call
        expr ::= compare
        expr ::= dict
        expr ::= generator_exp
        expr ::= list
        expr ::= or
        expr ::= subscript
        expr ::= subscript2
        expr ::= unary_not
        expr ::= unary_op
        expr ::= yield

        # bin_op (formerly "binary_expr") is the Python AST BinOp
        bin_op      ::= expr expr binary_operator

        binary_operator   ::= BINARY_ADD
        binary_operator   ::= BINARY_MULTIPLY
        binary_operator   ::= BINARY_AND
        binary_operator   ::= BINARY_OR
        binary_operator   ::= BINARY_XOR
        binary_operator   ::= BINARY_SUBTRACT
        binary_operator   ::= BINARY_TRUE_DIVIDE
        binary_operator   ::= BINARY_FLOOR_DIVIDE
        binary_operator   ::= BINARY_MODULO
        binary_operator   ::= BINARY_LSHIFT
        binary_operator   ::= BINARY_RSHIFT
        binary_operator   ::= BINARY_POWER

        # unary_op (formerly "unary_expr") is the Python AST UnaryOp
        unary_op          ::= expr unary_operator
        unary_operator    ::= UNARY_POSITIVE
        unary_operator    ::= UNARY_NEGATIVE
        unary_operator    ::= UNARY_INVERT

        unary_not ::= expr UNARY_NOT

        subscript ::= expr expr BINARY_SUBSCR

        get_iter  ::= expr GET_ITER

        yield ::= expr YIELD_VALUE

        _lambda_body ::= lambda_body

        expr      ::= if_exp

        return_expr  ::= expr
        return_expr  ::= ret_and
        return_expr  ::= ret_or

        return_expr_or_cond ::= return_expr
        return_expr_or_cond ::= if_exp_ret

        stmt ::= return_expr_lambda

        return_expr_lambda ::= return_expr RETURN_VALUE_LAMBDA LAMBDA_MARKER
        return_expr_lambda ::= return_expr RETURN_VALUE_LAMBDA

        compare        ::= compare_chained
        compare        ::= compare_single
        compare_single ::= expr expr COMPARE_OP

        # A compare_chained is two comparisons like x <= y <= z
        compare_chained  ::= expr compared_chained_middle ROT_TWO POP_TOP _come_froms
        compare_chained_right ::= expr COMPARE_OP JUMP_FORWARD

        # Non-null kvlist items are broken out in the individual grammars
        kvlist ::=

        # Positional arguments in make_function
        pos_arg ::= expr
        """

    def p_function_def(self, args):
        """
        stmt               ::= function_def
        function_def       ::= mkfunc store
        stmt               ::= function_def_deco
        function_def_deco  ::= mkfuncdeco store
        mkfuncdeco         ::= expr mkfuncdeco CALL_FUNCTION_1
        mkfuncdeco         ::= expr mkfuncdeco0 CALL_FUNCTION_1
        mkfuncdeco0        ::= mkfunc
        load_closure       ::= load_closure LOAD_CLOSURE
        load_closure       ::= LOAD_CLOSURE
        """

    def p_generator_exp(self, args):
        """ """

    def p_jump(self, args):
        """
        _jump ::= JUMP_ABSOLUTE
        _jump ::= JUMP_FORWARD
        _jump ::= JUMP_BACK

        # Zero or more COME_FROMs - loops can have this
        _come_froms ::= COME_FROM*
        _come_froms ::= _come_froms COME_FROM_LOOP

        # One or more COME_FROMs - joins of tryelse's have this
        come_froms ::= COME_FROM+

        # Zero or one COME_FROM
        # And/or expressions have this
        come_from_opt ::= COME_FROM?
        """

    def p_augmented_assign(self, args):
        """
        stmt ::= aug_assign1
        stmt ::= aug_assign2

        # This is odd in that other aug_assign1's have only 3 slots
        # The store isn't used as that's supposed to be also
        # indicated in the first expr
        aug_assign1 ::= expr expr
                        inplace_op store
        aug_assign1 ::= expr expr
                        inplace_op ROT_THREE STORE_SUBSCR
        aug_assign2 ::= expr DUP_TOP LOAD_ATTR expr
                        inplace_op ROT_TWO STORE_ATTR

        inplace_op ::= INPLACE_ADD
        inplace_op ::= INPLACE_SUBTRACT
        inplace_op ::= INPLACE_MULTIPLY
        inplace_op ::= INPLACE_TRUE_DIVIDE
        inplace_op ::= INPLACE_FLOOR_DIVIDE
        inplace_op ::= INPLACE_MODULO
        inplace_op ::= INPLACE_POWER
        inplace_op ::= INPLACE_LSHIFT
        inplace_op ::= INPLACE_RSHIFT
        inplace_op ::= INPLACE_AND
        inplace_op ::= INPLACE_XOR
        inplace_op ::= INPLACE_OR
        """

    def p_assign(self, args):
        """
        stmt ::= assign
        assign ::= expr DUP_TOP designList
        assign ::= expr store

        stmt ::= assign2
        stmt ::= assign3
        assign2 ::= expr expr ROT_TWO store store
        assign3 ::= expr expr expr ROT_THREE ROT_TWO store store store
        """

    def p_forstmt(self, args):
        """
        get_for_iter ::= GET_ITER _come_froms FOR_ITER

        for_block ::= l_stmts_opt _come_froms JUMP_BACK

        forelsestmt ::= SETUP_LOOP expr get_for_iter store
                        for_block POP_BLOCK else_suite _come_froms

        forelselaststmt ::= SETUP_LOOP expr get_for_iter store
                for_block POP_BLOCK else_suitec _come_froms

        forelselaststmtl ::= SETUP_LOOP expr get_for_iter store
                for_block POP_BLOCK else_suitel _come_froms
        """

    def p_import20(self, args):
        """
        stmt ::= import
        stmt ::= import_from
        stmt ::= import_from_star
        stmt ::= importmultiple

        importlist ::= importlist alias
        importlist ::= alias
        alias      ::= IMPORT_NAME store
        alias      ::= IMPORT_FROM store
        alias      ::= IMPORT_NAME attributes store

        import           ::= LOAD_CONST LOAD_CONST alias
        import_from_star ::= LOAD_CONST LOAD_CONST IMPORT_NAME IMPORT_STAR
        import_from_star ::= LOAD_CONST LOAD_CONST IMPORT_NAME_ATTR IMPORT_STAR
        import_from      ::= LOAD_CONST LOAD_CONST IMPORT_NAME importlist POP_TOP
        importmultiple   ::= LOAD_CONST LOAD_CONST alias imports_cont

        imports_cont ::= import_cont+
        import_cont  ::= LOAD_CONST LOAD_CONST alias

        attributes   ::= LOAD_ATTR+
        """

    def p_import37(self, args):
        """
        # The 3.7base scanner adds IMPORT_NAME_ATTR
        alias            ::= IMPORT_NAME_ATTR attributes store
        alias            ::= IMPORT_NAME_ATTR store

        alias37          ::= IMPORT_NAME store
        alias37          ::= IMPORT_FROM store

        attribute37      ::= expr LOAD_METHOD

        import_as37      ::= LOAD_CONST LOAD_CONST importlist37 store POP_TOP
        import_from   ::= LOAD_CONST LOAD_CONST importlist POP_TOP
        import_from37    ::= LOAD_CONST LOAD_CONST IMPORT_NAME_ATTR importlist37 POP_TOP
        import_from_as37 ::= LOAD_CONST LOAD_CONST import_from_attr37 store POP_TOP


        # A single entry in a dotted import a.b.c.d
        import_one       ::= importlists ROT_TWO IMPORT_FROM
        import_one       ::= importlists ROT_TWO POP_TOP IMPORT_FROM

        # Semantic checks distinguish importattr37 from import_from_attr37
        # in the former the "from" slot in a prior LOAD_CONST is null.

        # Used in: import .. as ..
        importattr37      ::= IMPORT_NAME_ATTR IMPORT_FROM

        # Used in: from xx import .. as ..
        import_from_attr37 ::= IMPORT_NAME_ATTR IMPORT_FROM

        importlist37  ::= import_one
        importlist37  ::= importattr37
        importlist37  ::= alias37+

        importlists   ::= importlist37+

        stmt          ::= import_as37
        stmt          ::= import_from37
        stmt          ::= import_from_as37

        """

    def p_list_comprehension(self, args):
        """
        expr ::= list_comp

        list_iter ::= list_for
        list_iter ::= list_if
        list_iter ::= list_if_not
        list_iter ::= lc_body

        list_if ::= expr jmp_false list_iter
        list_if_not ::= expr jmp_true list_iter
        """

    def p_gen_comp37(self, args):
        """
        comp_iter ::= comp_for
        comp_body ::= gen_comp_body
        gen_comp_body ::= expr YIELD_VALUE POP_TOP

        comp_if  ::= expr jmp_false comp_iter
        """

    def p_store(self, args):
        """
        # Note. The below is right-recursive:
        designList ::= store store
        designList ::= store DUP_TOP designList

        ## Can we replace with left-recursive, and redo with:
        ##
        ##   designList  ::= designLists store store
        ##   designLists ::= designLists store DUP_TOP
        ##   designLists ::=
        ## Will need to redo semantic actiion

        store           ::= STORE_FAST
        store           ::= STORE_NAME
        store           ::= STORE_GLOBAL
        store           ::= STORE_DEREF
        store           ::= expr STORE_ATTR
        store           ::= store_subscript
        store_subscript ::= expr expr STORE_SUBSCR
        store           ::= unpack
        """

    def p_32on(self, args):
        """
        if_exp::= expr jmp_false expr jump_forward_else expr COME_FROM

        # compare_chained_right is used in a "chained_compare": x <= y <= z
        # used exclusively in compare_chained
        compare_chained_right ::= expr COMPARE_OP RETURN_VALUE
        compare_chained_right ::= expr COMPARE_OP RETURN_VALUE_LAMBDA

        # Python < 3.5 no POP BLOCK
        whileTruestmt  ::= SETUP_LOOP l_stmts_opt JUMP_BACK COME_FROM_LOOP

        # Python 3.5+ has jump optimization to remove the redundant
        # jump_excepts. But in 3.3 we need them added

        except_handler ::= JUMP_FORWARD COME_FROM_EXCEPT except_stmts
                           END_FINALLY

        tryelsestmt    ::= SETUP_EXCEPT suite_stmts_opt POP_BLOCK
                           except_handler else_suite
                           jump_excepts come_from_except_clauses

        jump_excepts   ::= jump_except+

        subscript2 ::= expr expr DUP_TOP_TWO BINARY_SUBSCR

        # FIXME: The below rule was in uncompyle6.
        # In decompyle6 though "_ifstmts_jump" is part of an "ifstmt"
        # where as the below rule is appropriate for an "ifelsesmt"
        # Investigate and reconcile
        # _ifstmts_jump ::= c_stmts_opt JUMP_FORWARD _come_froms

        kv3       ::= expr expr STORE_MAP
        """
        return

    def p_33on(self, args):
        """
        # Python 3.3+ adds yield from.
        expr          ::= yield_from
        yield_from    ::= expr GET_YIELD_FROM_ITER LOAD_CONST YIELD_FROM

        # We do the grammar hackery below for semantics
        # actions that want c_stmts_opt at index 1

        # Python 3.5+ has jump optimization to remove the redundant
        # jump_excepts. But in 3.3 we need them added

        try_except  ::= SETUP_EXCEPT suite_stmts_opt POP_BLOCK
                        except_handler
                        jump_excepts come_from_except_clauses
        """

    def p_34on(self, args):
        """
        whilestmt     ::= setup_loop testexpr returns come_froms POP_BLOCK COME_FROM_LOOP

        # Seems to be needed starting 3.4.4 or so
        while1stmt    ::= setup_loop l_stmts
                          COME_FROM JUMP_BACK POP_BLOCK COME_FROM_LOOP
        while1stmt    ::= setup_loop l_stmts
                          POP_BLOCK COME_FROM_LOOP

        # FIXME the below masks a bug in not detecting COME_FROM_LOOP
        # grammar rules with COME_FROM -> COME_FROM_LOOP already exist
        whileelsestmt     ::= setup_loop testexpr l_stmts_opt JUMP_BACK POP_BLOCK
                              else_suitel COME_FROM

        while1elsestmt    ::= setup_loop l_stmts JUMP_BACK _come_froms POP_BLOCK else_suitel
                              COME_FROM_LOOP

        # Python 3.4+ optimizes the trailing two JUMPS away

        _ifstmts_jump ::= c_stmts_opt JUMP_ABSOLUTE JUMP_FORWARD _come_froms
        """

    def p_35_on(self, args):
        """

        while1elsestmt ::= setup_loop l_stmts JUMP_BACK
                           POP_BLOCK else_suite COME_FROM_LOOP

        # The following rule is for Python 3.5+ where we can have stuff like
        # while ..
        #     if
        #     ...
        # the end of the if will jump back to the loop and there will be a COME_FROM
        # after the jump
        l_stmts ::= lastl_stmt come_froms l_stmts

        # Python 3.5+ Await statement
        expr       ::= await_expr
        await_expr ::= expr GET_AWAITABLE LOAD_CONST YIELD_FROM

        stmt       ::= await_stmt
        await_stmt ::= await_expr POP_TOP

        # Python 3.5+ async additions

        inplace_op ::= INPLACE_MATRIX_MULTIPLY
        binary_operator  ::= BINARY_MATRIX_MULTIPLY

        # Python 3.5+ does jump optimization
        # In <.3.5 the below is a JUMP_FORWARD to a JUMP_ABSOLUTE.

        return_if_stmt ::= return_expr RETURN_END_IF POP_BLOCK
        return_if_lambda   ::= RETURN_END_IF_LAMBDA COME_FROM

        jb_else     ::= JUMP_BACK ELSE
        jb_else     ::= JUMP_BACK COME_FROM
        ifelsestmtc ::= testexpr c_stmts_opt JUMP_FORWARD else_suitec
        ifelsestmtl ::= testexpr c_stmts_opt jb_else else_suitel

        # We want to keep the positions of the "then" and
        # "else" statements in "ifelstmtl" similar to others of this ilk.
        testexpr_cf ::= testexpr come_froms
        ifelsestmtl ::= testexpr_cf c_stmts_opt jb_else else_suitel

        # 3.5 Has jump optimization which can route the end of an
        # "if/then" back to a loop just before an else.
        jump_absolute_else ::= jb_else
        jump_absolute_else ::= CONTINUE ELSE

        # Our hacky "ELSE" determination doesn't do a good job and really
        # determine the start of an "else". It could also be the end of an
        # "if-then" which ends in a "continue". Perhaps with real control-flow
        # analysis we'll sort this out. Or call "ELSE" something more appropriate.
        _ifstmts_jump ::= c_stmts_opt ELSE

        # ifstmt ::= testexpr c_stmts_opt

        iflaststmt ::= testexpr c_stmts_opt JUMP_FORWARD
        """

    def p_37_async(self, args):
        """
        stmt     ::= async_for_stmt37
        stmt     ::= async_for_stmt
        stmt     ::= async_forelse_stmt

        async_for_stmt     ::= setup_loop expr
                               GET_AITER
                               SETUP_EXCEPT GET_ANEXT LOAD_CONST
                               YIELD_FROM
                               store
                               POP_BLOCK JUMP_FORWARD COME_FROM_EXCEPT DUP_TOP
                               LOAD_GLOBAL COMPARE_OP POP_JUMP_IF_TRUE
                               END_FINALLY COME_FROM
                               for_block
                               COME_FROM
                               POP_TOP POP_TOP POP_TOP POP_EXCEPT POP_TOP POP_BLOCK
                               COME_FROM_LOOP

        # Order of LOAD_CONST YIELD_FROM is switched from 3.6 to save a LOAD_CONST
        async_for_stmt37   ::= setup_loop expr
                               GET_AITER
                               _come_froms
                               SETUP_EXCEPT GET_ANEXT
                               LOAD_CONST YIELD_FROM
                               store
                               POP_BLOCK JUMP_BACK COME_FROM_EXCEPT DUP_TOP
                               LOAD_GLOBAL COMPARE_OP POP_JUMP_IF_TRUE
                               END_FINALLY for_block COME_FROM
                               POP_TOP POP_TOP POP_TOP POP_EXCEPT
                               POP_TOP POP_BLOCK
                               COME_FROM_LOOP

        async_forelse_stmt ::= setup_loop expr
                               GET_AITER
                               _come_froms
                               SETUP_EXCEPT GET_ANEXT LOAD_CONST
                               YIELD_FROM
                               store
                               POP_BLOCK JUMP_FORWARD COME_FROM_EXCEPT DUP_TOP
                               LOAD_GLOBAL COMPARE_OP POP_JUMP_IF_TRUE
                               END_FINALLY COME_FROM
                               for_block
                               COME_FROM
                               POP_TOP POP_TOP POP_TOP POP_EXCEPT POP_TOP POP_BLOCK
                               else_suite COME_FROM_LOOP
        """

    def p_37_chained(self, args):
        """
        testtrue         ::= compare_chained37
        testfalse        ::= compare_chained37_false

        compare_chained     ::= compare_chained37
        compare_chained     ::= compare_chained37_false

        compare_chained37   ::= expr compared_chained_middlea_37
        compare_chained37   ::= expr compared_chained_middlec_37

        compare_chained37_false  ::= expr compared_chained_middle_false_37
        compare_chained37_false  ::= expr compared_chained_middleb_false_37
        compare_chained37_false  ::= expr compare_chained_right_false_37

        compared_chained_middlea_37      ::= expr DUP_TOP ROT_THREE COMPARE_OP POP_JUMP_IF_FALSE
        compared_chained_middlea_37      ::= expr DUP_TOP ROT_THREE COMPARE_OP POP_JUMP_IF_FALSE
                                      compare_chained_righta_37 COME_FROM POP_TOP COME_FROM
        compared_chained_middleb_false_37 ::= expr DUP_TOP ROT_THREE COMPARE_OP POP_JUMP_IF_FALSE
                                      compare_chained_rightb_false_37 POP_TOP _jump COME_FROM

        compared_chained_middlec_37      ::= expr DUP_TOP ROT_THREE COMPARE_OP POP_JUMP_IF_FALSE
                                      compare_chained_righta_37 POP_TOP

        compared_chained_middle_false_37 ::= expr DUP_TOP ROT_THREE COMPARE_OP POP_JUMP_IF_FALSE
                                      compare_chained_rightc_37 POP_TOP JUMP_FORWARD COME_FROM
        compared_chained_middle_false_37 ::= expr DUP_TOP ROT_THREE COMPARE_OP POP_JUMP_IF_FALSE
                                      compare_chained_rightb_false_37 POP_TOP _jump COME_FROM

        compare_chained_right_false_37 ::= expr DUP_TOP ROT_THREE COMPARE_OP POP_JUMP_IF_FALSE
                                      compare_chained_righta_false_37 POP_TOP JUMP_BACK COME_FROM

        compare_chained_righta_37       ::= expr COMPARE_OP come_from_opt POP_JUMP_IF_TRUE JUMP_FORWARD
        compare_chained_righta_37       ::= expr COMPARE_OP come_from_opt POP_JUMP_IF_TRUE JUMP_BACK
        compare_chained_righta_false_37 ::= expr COMPARE_OP come_from_opt POP_JUMP_IF_FALSE jf_cfs

        compare_chained_rightb_false_37 ::= expr COMPARE_OP come_from_opt POP_JUMP_IF_FALSE JUMP_FORWARD COME_FROM
        compare_chained_rightb_false_37 ::= expr COMPARE_OP come_from_opt POP_JUMP_IF_FALSE JUMP_FORWARD

        compare_chained_rightc_37       ::= expr DUP_TOP ROT_THREE COMPARE_OP come_from_opt POP_JUMP_IF_FALSE
                                       compare_chained_righta_false_37 ELSE
        compare_chained_rightc_37       ::= expr DUP_TOP ROT_THREE COMPARE_OP come_from_opt POP_JUMP_IF_FALSE
                                       compare_chained_righta_false_37
        """

    def p_37_conditionals(self, args):
        """
        expr                       ::= if_exp37
        if_exp37                   ::= expr expr jf_cfs expr COME_FROM
        jf_cfs                     ::= JUMP_FORWARD _come_froms
        ifelsestmt                 ::= testexpr c_stmts_opt jf_cfs else_suite
                                       opt_come_from_except

        # This is probably more realistically an "ifstmt" (with a null else)
        # see _cmp() of python3.8/distutils/__pycache__/version.cpython-38.opt-1.pyc
        ifelsestmt                 ::= testexpr stmts jf_cfs else_suite_opt
                                       opt_come_from_except


        expr_pjit                  ::= expr POP_JUMP_IF_TRUE
        expr_jit                   ::= expr JUMP_IF_TRUE
        expr_jt                    ::= expr jmp_true

        jmp_false37                ::= POP_JUMP_IF_FALSE COME_FROM
        list_if                    ::= expr jmp_false37 list_iter
        list_iter                  ::= list_if37
        list_iter                  ::= list_if37_not
        list_if37                  ::= compare_chained37_false list_iter
        list_if37_not              ::= compare_chained37 list_iter

        _ifstmts_jump              ::= c_stmts_opt come_froms
        _ifstmts_jump              ::= COME_FROM c_stmts come_froms

        and_not                    ::= expr jmp_false expr POP_JUMP_IF_TRUE
        testfalse                  ::= and_not

        expr                       ::= if_exp_37a
        expr                       ::= if_exp_37b
        if_exp_37a                 ::= and_not expr JUMP_FORWARD come_froms expr COME_FROM
        if_exp_37b                 ::= expr jmp_false expr POP_JUMP_IF_FALSE
                                       jump_forward_else expr
        jmp_false_cf               ::= POP_JUMP_IF_FALSE COME_FROM
        comp_if                    ::= or jmp_false_cf comp_iter
        """

    def p_comprehension3(self, args):
        """
        # Python3 scanner adds LOAD_LISTCOMP. Python3 does list comprehension like
        # other comprehensions (set, dictionary).

        # Our "continue" heuristic -  in two successive JUMP_BACKS, the first
        # one may be a continue - sometimes classifies a JUMP_BACK
        # as a CONTINUE. The two are kind of the same in a comprehension.

        comp_for ::= expr get_for_iter store comp_iter CONTINUE
        comp_for ::= expr get_for_iter store comp_iter JUMP_BACK

        for_iter ::= _come_froms FOR_ITER

        list_comp ::= BUILD_LIST_0 list_iter
        lc_body   ::= expr LIST_APPEND

        list_for  ::= expr_or_arg
                      for_iter
                      store list_iter
                      jb_or_c _come_froms

        set_for   ::= expr_or_arg
                      for_iter
                      store set_iter
                      jb_or_c _come_froms

        # This is seen in PyPy, but possibly it appears on other Python 3?
        list_if     ::= expr jmp_false list_iter COME_FROM
        list_if_not ::= expr jmp_true list_iter COME_FROM

        jb_or_c ::= JUMP_BACK
        jb_or_c ::= CONTINUE

        stmt ::= set_comp_func

        # TODO: simplify this
        set_comp_func ::= BUILD_SET_0 LOAD_ARG for_iter store comp_iter
                          JUMP_BACK ending_return
        set_comp_func ::= BUILD_SET_0 LOAD_ARG for_iter store comp_iter
                          COME_FROM JUMP_BACK ending_return

        comp_body ::= dict_comp_body
        comp_body ::= set_comp_body
        dict_comp_body ::= expr expr MAP_ADD
        set_comp_body ::= expr SET_ADD

        # See also common Python p_list_comprehension
        """

    def p_dict_comp3(self, args):
        """ "
        expr ::= dict_comp
        stmt ::= dict_comp_func

        dict_comp_func ::= BUILD_MAP_0 LOAD_ARG for_iter store
                           comp_iter JUMP_BACK ending_return

        comp_iter     ::= comp_if
        comp_iter     ::= comp_if_not
        comp_if_not   ::= expr jmp_true comp_iter
        comp_iter     ::= comp_body

        expr_or_arg     ::= LOAD_ARG
        expr_or_arg     ::= expr
        """

    def p_expr3(self, args):
        """
        expr           ::= if_exp_not
        if_exp_not     ::= expr jmp_true  expr jump_forward_else expr COME_FROM

        # a JUMP_FORWARD to another JUMP_FORWARD can get turned into
        # a JUMP_ABSOLUTE with no COME_FROM
        if_exp         ::= expr jmp_false expr jump_absolute_else expr

        # if_exp_true are for conditions which always evaluate true
        # There is dead or non-optional remnants of the condition code though,
        # and we use that to match on to reconstruct the source more accurately
        expr           ::= if_exp_true
        if_exp_true    ::= expr JUMP_FORWARD expr COME_FROM
        """

    def p_generator_exp3(self, args):
        """
        load_genexpr ::= LOAD_GENEXPR
        load_genexpr ::= BUILD_TUPLE_1 LOAD_GENEXPR LOAD_STR
        """

    def p_grammar(self, args):
        """
        sstmt ::= stmt
        sstmt ::= ifelsestmtr
        sstmt ::= return RETURN_LAST

        return_if_stmts ::= return_if_stmt come_from_opt
        return_if_stmts ::= _stmts return_if_stmt _come_froms
        return_if_stmt  ::= return_expr RETURN_END_IF
        returns         ::= _stmts return_if_stmt

        stmt      ::= break
        break     ::= BREAK_LOOP

        stmt      ::= continue
        continue  ::= CONTINUE
        continues ::= _stmts lastl_stmt continue
        continues ::= lastl_stmt continue
        continues ::= continue


        kwarg      ::= LOAD_STR expr
        kwargs     ::= kwarg+

        classdef ::= build_class store

        # FIXME: we need to add these because don't detect this properly
        # in custom rules. Specifically if one of the exprs is CALL_FUNCTION
        # then we'll mistake that for the final CALL_FUNCTION.
        # We can fix by triggering on the CALL_FUNCTION op
        # Python3 introduced LOAD_BUILD_CLASS
        # Other definitions are in a custom rule
        build_class ::= LOAD_BUILD_CLASS mkfunc expr call CALL_FUNCTION_3
        build_class ::= LOAD_BUILD_CLASS mkfunc expr call expr CALL_FUNCTION_4

        stmt ::= classdefdeco
        classdefdeco ::= classdefdeco1 store

        # In 3.7 there are some LOAD_GLOBALs we don't convert to LOAD_ASSERT
        stmt    ::= assert2
        assert2 ::= expr jmp_true LOAD_GLOBAL expr CALL_FUNCTION_1 RAISE_VARARGS_1

        # "assert_invert" tests on the negative of the condition given
        stmt          ::= assert_invert
        assert_invert ::= testtrue LOAD_GLOBAL RAISE_VARARGS_1

        expr    ::= LOAD_ASSERT

        # FIXME: add this:
        # expr    ::= assert_expr_or

        ifstmt ::= testexpr _ifstmts_jump

        testexpr ::= testfalse
        testexpr ::= testtrue
        testfalse ::= expr jmp_false
        testtrue ::= expr jmp_true

        _ifstmts_jump ::= return_if_stmts
        _ifstmts_jump ::= c_stmts_opt COME_FROM

        iflaststmt  ::= testexpr c_stmts
        iflaststmt  ::= testexpr c_stmts JUMP_ABSOLUTE

        iflaststmtl ::= testexpr c_stmts JUMP_BACK
        iflaststmtl ::= testexpr c_stmts JUMP_BACK COME_FROM_LOOP
        iflaststmtl ::= testexpr c_stmts JUMP_BACK POP_BLOCK

        # These are used to keep parse tree indices the same
        jump_forward_else  ::= JUMP_FORWARD
        jump_forward_else  ::= JUMP_FORWARD ELSE
        jump_forward_else  ::= JUMP_FORWARD COME_FROM
        jump_absolute_else ::= JUMP_ABSOLUTE ELSE
        jump_absolute_else ::= JUMP_ABSOLUTE _come_froms
        jump_absolute_else ::= come_froms _jump COME_FROM

        # Note: in if/else kinds of statements, we err on the side
        # of missing "else" clauses. Therefore we include grammar
        # rules with and without ELSE.

        ifelsestmt ::= testexpr c_stmts_opt JUMP_FORWARD
                       else_suite opt_come_from_except
        ifelsestmt ::= testexpr c_stmts_opt jump_forward_else
                       else_suite _come_froms

        # This handles the case where a "JUMP_ABSOLUTE" is part
        # of an inner if in c_stmts_opt
        ifelsestmt ::= testexpr c_stmts come_froms
                       else_suite come_froms

        # ifelsestmt ::= testexpr c_stmts_opt jump_forward_else
        #                pass  _come_froms

        ifelsestmtc ::= testexpr c_stmts_opt JUMP_ABSOLUTE else_suitec
        ifelsestmtc ::= testexpr c_stmts_opt jump_absolute_else else_suitec

        ifelsestmtr ::= testexpr return_if_stmts returns

        ifelsestmtl ::= testexpr c_stmts_opt cf_jump_back else_suitel

        cf_jump_back ::= COME_FROM JUMP_BACK

        # FIXME: this feels like a hack. Is it just 1 or two
        # COME_FROMs?  the parsed tree for this and even with just the
        # one COME_FROM for Python 2.7 seems to associate the
        # COME_FROM targets from the wrong places

        # this is nested inside a try_except
        tryfinallystmt ::= SETUP_FINALLY suite_stmts_opt
                           POP_BLOCK LOAD_CONST
                           COME_FROM_FINALLY suite_stmts_opt END_FINALLY

        except_handler ::= jmp_abs COME_FROM except_stmts
                           _come_froms END_FINALLY
        except_handler ::= jmp_abs COME_FROM_EXCEPT except_stmts
                           _come_froms END_FINALLY

        # FIXME: remove this
        except_handler ::= JUMP_FORWARD COME_FROM except_stmts
                           come_froms END_FINALLY come_from_opt

        except_stmts   ::= except_stmt+

        except_stmt    ::= except_cond1 except_suite come_from_opt
        except_stmt    ::= except_cond2 except_suite come_from_opt
        except_stmt    ::= except_cond2 except_suite_finalize
        except_stmt    ::= except

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

        except_var_finalize ::= POP_BLOCK POP_EXCEPT LOAD_CONST COME_FROM_FINALLY
                                LOAD_CONST store delete

        except_suite ::= returns

        except_cond1 ::= DUP_TOP expr COMPARE_OP
                         jmp_false POP_TOP POP_TOP POP_TOP

        except_cond2 ::= DUP_TOP expr COMPARE_OP
                         jmp_false POP_TOP store POP_TOP come_from_opt

        except  ::=  POP_TOP POP_TOP POP_TOP c_stmts_opt POP_EXCEPT _jump
        except  ::=  POP_TOP POP_TOP POP_TOP returns

        jmp_abs ::= JUMP_ABSOLUTE
        jmp_abs ::= JUMP_BACK

        """

    def p_misc3(self, args):
        """
        except_handler ::= JUMP_FORWARD COME_FROM_EXCEPT except_stmts
                           come_froms END_FINALLY

        for_block ::= l_stmts_opt COME_FROM_LOOP JUMP_BACK
        for_block ::= l_stmts
        for_block ::= l_stmts JUMP_BACK
        iflaststmtl ::= testexpr c_stmts
        """

    def p_come_from3(self, args):
        """
        opt_come_from_except ::= COME_FROM_EXCEPT
        opt_come_from_except ::= _come_froms
        opt_come_from_except ::= come_from_except_clauses

        come_from_except_clauses ::= COME_FROM_EXCEPT_CLAUSE+
        """

    def p_jump3(self, args):
        """
        jmp_false ::= POP_JUMP_IF_FALSE
        jmp_true  ::= POP_JUMP_IF_TRUE

        # FIXME: Common with 2.7
        ret_and    ::= expr JUMP_IF_FALSE_OR_POP return_expr_or_cond COME_FROM
        ret_or     ::= expr JUMP_IF_TRUE_OR_POP return_expr_or_cond COME_FROM
        if_exp_ret ::= expr POP_JUMP_IF_FALSE expr RETURN_END_IF COME_FROM return_expr_or_cond

        jitop_come_from_expr ::= JUMP_IF_TRUE_OR_POP come_froms expr
        jifop_come_from ::= JUMP_IF_FALSE_OR_POP come_froms
        expr_jitop      ::= expr JUMP_IF_TRUE_OR_POP

        or        ::= and jitop_come_from_expr COME_FROM
        or        ::= expr_jitop  expr COME_FROM
        or        ::= expr_jit expr COME_FROM
        or        ::= expr_pjit expr POP_JUMP_IF_FALSE COME_FROM

        testfalse_not_or   ::= expr jmp_false expr jmp_false COME_FROM
        testfalse_not_and ::= and jmp_true come_froms

        testfalse_not_and ::= expr jmp_false expr jmp_true  COME_FROM
        testfalse ::= testfalse_not_or
        testfalse ::= testfalse_not_and
        testfalse ::= or jmp_false COME_FROM

        iflaststmtl ::= testexprl c_stmts JUMP_BACK
        iflaststmtl ::= testexprl c_stmts JUMP_BACK COME_FROM_LOOP
        iflaststmtl ::= testexprl c_stmts JUMP_BACK POP_BLOCK
        testexprl   ::= testfalsel
        testfalsel  ::= expr jmp_true

        or          ::= expr_jt expr

        and  ::= expr JUMP_IF_FALSE_OR_POP expr come_from_opt
        and  ::= expr jifop_come_from expr

        expr_pjit_come_from ::= expr POP_JUMP_IF_TRUE COME_FROM
        or  ::= expr_pjit_come_from expr

        ## Note that "jmp_false" is what we check on in the "and" reduce rule.
        and ::= expr jmp_false expr COME_FROM
        or  ::= expr_jt  expr COME_FROM

        # compared_chained_middle is used exclusively in chained_compare
        compared_chained_middle ::= expr DUP_TOP ROT_THREE COMPARE_OP JUMP_IF_FALSE_OR_POP
                                    compared_chained_middle COME_FROM
        compared_chained_middle ::= expr DUP_TOP ROT_THREE COMPARE_OP JUMP_IF_FALSE_OR_POP
                                    compare_chained_right COME_FROM
        """

    def p_stmt3(self, args):
        """
        stmt               ::= if_exp_lambda
        stmt               ::= if_exp_not_lambda

        # If statement inside a loop:
        stmt               ::= ifstmtl

        if_exp_lambda      ::= expr jmp_false expr return_if_lambda
                               return_stmt_lambda LAMBDA_MARKER
        if_exp_not_lambda
                           ::= expr jmp_true expr return_if_lambda
                               return_stmt_lambda LAMBDA_MARKER

        return_stmt_lambda ::= return_expr RETURN_VALUE_LAMBDA
        return_if_lambda   ::= RETURN_END_IF_LAMBDA

        stmt               ::= return_closure
        return_closure     ::= LOAD_CLOSURE RETURN_VALUE RETURN_LAST

        stmt               ::= whileTruestmt
        ifelsestmt         ::= testexpr c_stmts_opt JUMP_FORWARD else_suite _come_froms
        ifelsestmtl        ::= testexpr c_stmts_opt jump_forward_else else_suitec

        ifstmtl            ::= testexpr _ifstmts_jumpl

        _ifstmts_jumpl     ::= c_stmts JUMP_BACK
        _ifstmts_jumpl     ::= _ifstmts_jump

        # The following can happen when the jump offset is large and
        # Python is looking to do a small jump to a larger jump to get
        # around the problem that the offset can't be represented in
        # the size allowed for the jump offset. This is more likely to
        # happen in wordcode Python since the offset range has been
        # reduced.  FIXME: We should add a reduction check that the
        # final jump goes to another jump.

        _ifstmts_jumpl     ::= COME_FROM c_stmts JUMP_BACK
        _ifstmts_jumpl     ::= COME_FROM c_stmts JUMP_FORWARD

        """

    def p_loop_stmt3(self, args):
        """
        setup_loop        ::= SETUP_LOOP _come_froms
        for               ::= setup_loop expr get_for_iter store for_block POP_BLOCK
        for               ::= setup_loop expr get_for_iter store for_block POP_BLOCK
                              COME_FROM_LOOP


        forelsestmt       ::= setup_loop expr get_for_iter store for_block POP_BLOCK else_suite
                              COME_FROM_LOOP

        forelselaststmt   ::= setup_loop expr get_for_iter store for_block POP_BLOCK else_suitec
                              COME_FROM_LOOP

        forelselaststmtl  ::= setup_loop expr get_for_iter store for_block POP_BLOCK else_suitel
                              COME_FROM_LOOP

        whilestmt         ::= setup_loop testexpr l_stmts_opt COME_FROM JUMP_BACK POP_BLOCK
                              COME_FROM_LOOP


        whilestmt         ::= setup_loop testexpr l_stmts_opt JUMP_BACK POP_BLOCK
                              COME_FROM_LOOP

        whilestmt         ::= setup_loop testexpr returns          POP_BLOCK
                              COME_FROM_LOOP

        # We can be missing a COME_FROM_LOOP if the "while" statement is nested inside an if/else
        # so after the POP_BLOCK we have a JUMP_FORWARD which forms the "else" portion of the "if"
        # This is undoubtedly some sort of JUMP optimization going on.

        whilestmt         ::= setup_loop testexpr l_stmts_opt JUMP_BACK come_froms
                              POP_BLOCK

        while1elsestmt    ::= setup_loop          l_stmts     JUMP_BACK
                              else_suitel

        whileelsestmt     ::= setup_loop testexpr l_stmts_opt JUMP_BACK POP_BLOCK
                              else_suitel COME_FROM_LOOP

        whileTruestmt     ::= setup_loop l_stmts_opt          JUMP_BACK POP_BLOCK
                              _come_froms

        # FIXME: Python 3.? starts adding branch optimization? Put this starting there.

        while1stmt        ::= setup_loop l_stmts COME_FROM_LOOP
        while1stmt        ::= setup_loop l_stmts COME_FROM_LOOP JUMP_BACK POP_BLOCK COME_FROM_LOOP
        while1stmt        ::= setup_loop l_stmts COME_FROM JUMP_BACK COME_FROM_LOOP

        while1elsestmt    ::= setup_loop l_stmts JUMP_BACK
                              else_suite COME_FROM_LOOP

        # FIXME: investigate - can code really produce a NOP?
        for               ::= setup_loop expr get_for_iter store for_block POP_BLOCK NOP
                              COME_FROM_LOOP
        """

    def p_36misc(self, args):
        """
        sstmt ::= sstmt RETURN_LAST

        # 3.6 redoes how return_closure works. FIXME: Isolate to LOAD_CLOSURE
        return_closure   ::= LOAD_CLOSURE DUP_TOP STORE_NAME RETURN_VALUE RETURN_LAST

        for_block       ::= l_stmts_opt come_from_loops JUMP_BACK
        come_from_loops ::= COME_FROM_LOOP*

        whilestmt       ::= setup_loop testexpr l_stmts_opt
                            JUMP_BACK come_froms POP_BLOCK COME_FROM_LOOP
        whilestmt       ::= setup_loop testexpr l_stmts_opt
                            come_froms JUMP_BACK come_froms POP_BLOCK COME_FROM_LOOP

        # 3.6 due to jump optimization, we sometimes add RETURN_END_IF where
        # RETURN_VALUE is meant. Specifically this can happen in
        # ifelsestmt -> ...else_suite _. suite_stmts... (last) stmt
        return ::= return_expr RETURN_END_IF
        return ::= return_expr RETURN_VALUE COME_FROM
        return_stmt_lambda ::= return_expr RETURN_VALUE_LAMBDA COME_FROM

        # A COME_FROM is dropped off because of JUMP-to-JUMP optimization
        and  ::= expr jmp_false expr
        and  ::= expr jmp_false expr jmp_false

        jf_cf       ::= JUMP_FORWARD COME_FROM
        cf_jf_else  ::= come_froms JUMP_FORWARD ELSE

        if_exp ::= expr jmp_false expr jf_cf expr COME_FROM

        async_for_stmt     ::= setup_loop expr
                               GET_AITER
                               LOAD_CONST YIELD_FROM SETUP_EXCEPT GET_ANEXT LOAD_CONST
                               YIELD_FROM
                               store
                               POP_BLOCK JUMP_FORWARD COME_FROM_EXCEPT DUP_TOP
                               LOAD_GLOBAL COMPARE_OP POP_JUMP_IF_FALSE
                               POP_TOP POP_TOP POP_TOP POP_EXCEPT POP_BLOCK
                               JUMP_ABSOLUTE END_FINALLY COME_FROM
                               for_block POP_BLOCK
                               COME_FROM_LOOP

        # Adds a COME_FROM_ASYNC_WITH over 3.5
        # FIXME: remove corresponding rule for 3.5?

        except_suite ::= c_stmts_opt COME_FROM POP_EXCEPT jump_except COME_FROM

        jb_cfs      ::= come_from_opt JUMP_BACK come_froms
        ifelsestmtl ::= testexpr c_stmts_opt jb_cfs else_suitel
        ifelsestmtl ::= testexpr c_stmts_opt cf_jf_else else_suitel

        # In 3.6+, A sequence of statements ending in a RETURN can cause
        # JUMP_FORWARD END_FINALLY to be omitted from try middle

        except_return    ::= POP_TOP POP_TOP POP_TOP returns
        except_handler   ::= JUMP_FORWARD COME_FROM_EXCEPT except_return

        # Try middle following a returns
        except_handler36 ::= COME_FROM_EXCEPT except_stmts END_FINALLY

        stmt             ::= try_except36
        try_except36     ::= SETUP_EXCEPT returns except_handler36
                             opt_come_from_except
        try_except36     ::= SETUP_EXCEPT suite_stmts
        try_except36     ::= SETUP_EXCEPT suite_stmts_opt POP_BLOCK
                             except_handler36 come_from_opt

        # 3.6 omits END_FINALLY sometimes
        except_handler36 ::= COME_FROM_EXCEPT except_stmts
        except_handler36 ::= JUMP_FORWARD COME_FROM_EXCEPT except_stmts
        except_handler   ::= jmp_abs COME_FROM_EXCEPT except_stmts

        stmt             ::= tryfinally36
        tryfinally36     ::= SETUP_FINALLY returns
                             COME_FROM_FINALLY suite_stmts
        tryfinally36     ::= SETUP_FINALLY returns
                             COME_FROM_FINALLY suite_stmts_opt END_FINALLY
        except_suite_finalize ::= SETUP_FINALLY returns
                                  COME_FROM_FINALLY suite_stmts_opt END_FINALLY _jump

        stmt ::= tryfinally_return_stmt
        tryfinally_return_stmt ::= SETUP_FINALLY suite_stmts_opt POP_BLOCK LOAD_CONST
                                   COME_FROM_FINALLY

        compare_chained_right ::= expr COMPARE_OP come_froms JUMP_FORWARD
        """

    def p_37_misc(self, args):
        """
        # long except clauses in a loop can sometimes cause a JUMP_BACK to turn into a
        # JUMP_FORWARD to a JUMP_BACK. And when this happens there is an additional
        # ELSE added to the except_suite. With better flow control perhaps we can
        # sort this out better.
        except_suite ::= c_stmts_opt POP_EXCEPT jump_except ELSE

        # FIXME: the below is to work around test_grammar expecting a "call" to be
        # on the LHS because it is also somewhere on in a rule.
        call        ::= expr CALL_METHOD_0
        """

    def customize_grammar_rules(self, tokens, customize):
        super(Python37Parser, self).customize_grammar_rules(tokens, customize)
        self.check_reduce["call_kw"] = "AST"

        # Opcode names in the custom_ops_processed set have rules that get added
        # unconditionally and the rules are constant. So they need to be done
        # only once and if we see the opcode a second we don't have to consider
        # adding more rules.
        #
        # Note: BUILD_TUPLE_UNPACK_WITH_CALL gets considered by
        # default because it starts with BUILD. So we'll set to ignore it from
        # the start.
        custom_ops_processed = set()

        for i, token in enumerate(tokens):
            opname = token.kind

            if opname == "LOAD_ASSERT":
                if "PyPy" in customize:
                    rules_str = """
                    stmt ::= JUMP_IF_NOT_DEBUG stmts COME_FROM
                    """
                    self.add_unique_doc_rules(rules_str, customize)
            elif opname == "FORMAT_VALUE":
                rules_str = """
                    expr              ::= formatted_value1
                    formatted_value1  ::= expr FORMAT_VALUE
                """
                self.add_unique_doc_rules(rules_str, customize)
            elif opname == "FORMAT_VALUE_ATTR":
                rules_str = """
                expr              ::= formatted_value2
                formatted_value2  ::= expr expr FORMAT_VALUE_ATTR
                """
                self.add_unique_doc_rules(rules_str, customize)
            elif opname == "MAKE_FUNCTION_CLOSURE":
                if "LOAD_DICTCOMP" in self.seen_ops:
                    # Is there something general going on here?
                    rule = """
                       dict_comp ::= load_closure LOAD_DICTCOMP LOAD_STR
                                     MAKE_FUNCTION_CLOSURE expr
                                     GET_ITER CALL_FUNCTION_1
                       """
                    self.addRule(rule, nop_func)
                elif "LOAD_SETCOMP" in self.seen_ops:
                    rule = """
                       set_comp ::= load_closure LOAD_SETCOMP LOAD_STR
                                    MAKE_FUNCTION_CLOSURE expr
                                    GET_ITER CALL_FUNCTION_1
                       """
                    self.addRule(rule, nop_func)

            elif opname == "BEFORE_ASYNC_WITH":
                rules_str = """
                  stmt               ::= async_with_stmt SETUP_ASYNC_WITH
                  async_with_pre     ::= BEFORE_ASYNC_WITH GET_AWAITABLE LOAD_CONST YIELD_FROM SETUP_ASYNC_WITH
                  async_with_post    ::= COME_FROM_ASYNC_WITH
                                         WITH_CLEANUP_START GET_AWAITABLE LOAD_CONST YIELD_FROM
                                         WITH_CLEANUP_FINISH END_FINALLY

                  stmt               ::= async_with_as_stmt
                  async_with_as_stmt ::= expr
                                         async_with_pre
                                         store
                                         suite_stmts_opt
                                         POP_BLOCK LOAD_CONST
                                         async_with_post

                 async_with_stmt     ::= expr
                                         async_with_pre
                                         POP_TOP
                                         suite_stmts_opt
                                         POP_BLOCK LOAD_CONST
                                         async_with_post
                 async_with_stmt     ::= expr
                                         async_with_pre
                                         POP_TOP
                                         suite_stmts_opt
                                         async_with_post
                """
                self.addRule(rules_str, nop_func)

            elif opname.startswith("BUILD_STRING"):
                v = token.attr
                rules_str = """
                    expr                 ::= joined_str
                    joined_str           ::= %sBUILD_STRING_%d
                """ % (
                    "expr " * v,
                    v,
                )
                self.add_unique_doc_rules(rules_str, customize)
                if "FORMAT_VALUE_ATTR" in self.seen_ops:
                    rules_str = """
                      formatted_value_attr ::= expr expr FORMAT_VALUE_ATTR expr BUILD_STRING
                      expr                 ::= formatted_value_attr
                    """
                    self.add_unique_doc_rules(rules_str, customize)
            elif opname.startswith("BUILD_MAP_UNPACK_WITH_CALL"):
                v = token.attr
                rule = "build_map_unpack_with_call ::= %s%s" % ("expr " * v, opname)
                self.addRule(rule, nop_func)
            elif opname.startswith("BUILD_TUPLE_UNPACK_WITH_CALL"):
                v = token.attr
                rule = (
                    "build_tuple_unpack_with_call ::= "
                    + "expr1024 " * int(v // 1024)
                    + "expr32 " * int((v // 32) % 32)
                    + "expr " * (v % 32)
                    + opname
                )
                self.addRule(rule, nop_func)
                rule = "starred ::= %s %s" % ("expr " * v, opname)
                self.addRule(rule, nop_func)

            elif opname == "GET_AITER":
                self.add_unique_doc_rules("get_aiter ::= expr GET_AITER", customize)

                if not {"MAKE_FUNCTION_0", "MAKE_FUNCTION_CLOSURE"} in self.seen_ops:
                    self.addRule(
                        """
                        expr                ::= dict_comp_async
                        expr                ::= generator_exp_async
                        expr                ::= list_comp_async

                        dict_comp_async     ::= LOAD_DICTCOMP
                                                LOAD_STR
                                                MAKE_FUNCTION_0
                                                get_aiter
                                                CALL_FUNCTION_1

                        dict_comp_async     ::= BUILD_MAP_0 LOAD_ARG
                                                dict_comp_async

                        func_async_middle   ::= POP_BLOCK JUMP_FORWARD COME_FROM_EXCEPT
                                                DUP_TOP LOAD_GLOBAL COMPARE_OP POP_JUMP_IF_TRUE
                                                END_FINALLY COME_FROM

                        func_async_prefix   ::= _come_froms SETUP_EXCEPT GET_ANEXT LOAD_CONST YIELD_FROM

                        generator_exp_async ::= load_genexpr LOAD_STR MAKE_FUNCTION_0
                                                get_aiter CALL_FUNCTION_1

                        genexpr_func_async  ::= LOAD_ARG func_async_prefix
                                                store func_async_middle comp_iter
                                                JUMP_BACK COME_FROM
                                                POP_TOP POP_TOP POP_TOP POP_EXCEPT POP_TOP

                        # FIXME this is a workaround for probably some bug in the Earley parser
                        # if we use get_aiter, then list_comp_async doesn't match, and I don't
                        # understand why.
                        expr_get_aiter      ::= expr GET_AITER

                        list_afor           ::= get_aiter list_afor2

                        list_afor2          ::= func_async_prefix
                                                store func_async_middle list_iter
                                                JUMP_BACK COME_FROM
                                                POP_TOP POP_TOP POP_TOP POP_EXCEPT POP_TOP

                        list_comp_async     ::= BUILD_LIST_0 LOAD_ARG list_afor2
                        list_comp_async     ::= LOAD_LISTCOMP LOAD_STR MAKE_FUNCTION_0
                                                expr_get_aiter CALL_FUNCTION_1
                                                GET_AWAITABLE LOAD_CONST
                                                YIELD_FROM

                        list_iter           ::= list_afor

                        set_comp_async       ::= LOAD_SETCOMP
                                                 LOAD_STR
                                                 MAKE_FUNCTION_0
                                                 get_aiter
                                                 CALL_FUNCTION_1

                        set_comp_async       ::= LOAD_CLOSURE
                                                 BUILD_TUPLE_1
                                                 LOAD_SETCOMP
                                                 LOAD_STR MAKE_FUNCTION_CLOSURE
                                                 get_aiter CALL_FUNCTION_1
                                                 await
                       """,
                        nop_func,
                    )
                    custom_ops_processed.add(opname)

                self.addRule(
                    """
                    dict_comp_async      ::= BUILD_MAP_0 LOAD_ARG
                                             dict_comp_async

                    expr                 ::= dict_comp_async
                    expr                 ::= generator_exp_async
                    expr                 ::= list_comp_async
                    expr                 ::= set_comp_async

                    func_async_middle   ::= POP_BLOCK JUMP_FORWARD COME_FROM_EXCEPT
                                            DUP_TOP LOAD_GLOBAL COMPARE_OP POP_JUMP_IF_TRUE
                                            END_FINALLY _come_froms

                    # async_iter         ::= block_break SETUP_EXCEPT GET_ANEXT LOAD_CONST YIELD_FROM

                    get_aiter            ::= expr GET_AITER

                    list_afor            ::= get_aiter list_afor2

                    list_comp_async      ::= BUILD_LIST_0 LOAD_ARG list_afor2
                    list_iter            ::= list_afor


                    set_afor             ::= get_aiter set_afor2
                    set_iter             ::= set_afor
                    set_iter             ::= set_for

                    set_comp_async       ::= BUILD_SET_0 LOAD_ARG
                                             set_comp_async

                   """,
                    nop_func,
                )
                custom_ops_processed.add(opname)

            elif opname == "GET_ANEXT":
                self.addRule(
                    """
                    expr                 ::= genexpr_func_async
                    expr                 ::= BUILD_MAP_0 genexpr_func_async
                    expr                 ::= list_comp_async

                    dict_comp_async      ::= BUILD_MAP_0 genexpr_func_async

                    async_iter           ::= _come_froms
                                             SETUP_EXCEPT GET_ANEXT LOAD_CONST YIELD_FROM

                    store_async_iter_end ::= store
                                             POP_BLOCK JUMP_FORWARD COME_FROM_EXCEPT
                                             DUP_TOP LOAD_GLOBAL COMPARE_OP POP_JUMP_IF_TRUE
                                             END_FINALLY COME_FROM

                    # We use store_async_iter_end to make comp_iter come out in the right position,
                    # (after the logical "store")
                    genexpr_func_async   ::= LOAD_ARG async_iter
                                             store_async_iter_end
                                             comp_iter
                                             JUMP_BACK COME_FROM
                                             POP_TOP POP_TOP POP_TOP POP_EXCEPT POP_TOP

                    list_afor2           ::= async_iter
                                             store
                                             list_iter
                                             JUMP_BACK
                                             COME_FROM_FINALLY
                                             END_ASYNC_FOR

                    list_comp_async      ::= BUILD_LIST_0 LOAD_ARG list_afor2

                    set_afor2            ::= async_iter
                                             store
                                             func_async_middle
                                             set_iter
                                             JUMP_BACK COME_FROM
                                             POP_TOP POP_TOP POP_TOP POP_EXCEPT POP_TOP

                    set_afor2            ::= expr_or_arg
                                             set_iter_async

                    set_comp_async       ::= BUILD_SET_0 set_afor2

                    set_iter_async       ::= async_iter
                                             store
                                             set_iter
                                             JUMP_BACK
                                             _come_froms
                                             END_ASYNC_FOR

                    return_expr_lambda   ::= genexpr_func_async
                                             LOAD_CONST RETURN_VALUE
                                             RETURN_VALUE_LAMBDA

                    return_expr_lambda   ::= BUILD_SET_0 genexpr_func_async
                                             RETURN_VALUE_LAMBDA LAMBDA_MARKER
                   """,
                    nop_func,
                )
                custom_ops_processed.add(opname)

            elif opname == "GET_AWAITABLE":
                rule_str = """
                    await_expr ::= expr GET_AWAITABLE LOAD_CONST YIELD_FROM
                    expr       ::= await_expr
                """
                self.add_unique_doc_rules(rule_str, customize)

            elif opname == "GET_ITER":
                self.addRule(
                    """
                    expr      ::= get_iter
                    get_iter  ::= expr GET_ITER
                    """,
                    nop_func,
                )
                custom_ops_processed.add(opname)

            elif opname == "LOAD_ASSERT":
                if "PyPy" in customize:
                    rules_str = """
                    stmt ::= JUMP_IF_NOT_DEBUG stmts COME_FROM
                    """
                    self.add_unique_doc_rules(rules_str, customize)

            elif opname == "LOAD_ATTR":
                self.addRule(
                    """
                  expr      ::= attribute
                  attribute ::= expr LOAD_ATTR
                  """,
                    nop_func,
                )
                custom_ops_processed.add(opname)

            elif opname == "SETUP_WITH":
                rules_str = """
                with       ::= expr SETUP_WITH POP_TOP suite_stmts_opt COME_FROM_WITH
                               WITH_CLEANUP_START WITH_CLEANUP_FINISH END_FINALLY

                # Removes POP_BLOCK LOAD_CONST from 3.6-
                with_as    ::= expr SETUP_WITH store suite_stmts_opt COME_FROM_WITH
                               WITH_CLEANUP_START WITH_CLEANUP_FINISH END_FINALLY
                """
                if self.version < (3, 8):
                    rules_str += """
                    with       ::= expr SETUP_WITH POP_TOP suite_stmts_opt POP_BLOCK
                                   LOAD_CONST
                                   WITH_CLEANUP_START WITH_CLEANUP_FINISH END_FINALLY
                    """
                else:
                    rules_str += """
                    with       ::= expr SETUP_WITH POP_TOP suite_stmts_opt POP_BLOCK
                                   BEGIN_FINALLY COME_FROM_WITH
                                   WITH_CLEANUP_START WITH_CLEANUP_FINISH
                                   END_FINALLY
                    """
                self.addRule(rules_str, nop_func)
                pass
            pass

    def custom_classfunc_rule(self, opname, token, customize, next_token):
        args_pos, args_kw = self.get_pos_kw(token)

        # Additional exprs for * and ** args:
        #  0 if neither
        #  1 for CALL_FUNCTION_VAR or CALL_FUNCTION_KW
        #  2 for * and ** args (CALL_FUNCTION_VAR_KW).
        # Yes, this computation based on instruction name is a little bit hoaky.
        nak = (len(opname) - len("CALL_FUNCTION")) // 3
        uniq_param = args_kw + args_pos

        if frozenset(("GET_AWAITABLE", "YIELD_FROM")).issubset(self.seen_ops):
            rule = (
                """
                await      ::= GET_AWAITABLE LOAD_CONST YIELD_FROM
                await_expr ::= expr await
                expr       ::= await_expr
                async_call ::= expr """
                + ("pos_arg " * args_pos)
                + ("kwarg " * args_kw)
                + "expr " * nak
                + token.kind
                + " GET_AWAITABLE LOAD_CONST YIELD_FROM"
            )
            self.add_unique_doc_rules(rule, customize)
            self.add_unique_rule(
                "expr ::= async_call", token.kind, uniq_param, customize
            )

        if opname.startswith("CALL_FUNCTION_KW"):
            self.addRule("expr ::= call_kw36", nop_func)
            values = "expr " * token.attr
            rule = "call_kw36 ::= expr {values} LOAD_CONST {opname}".format(**locals())
            self.add_unique_rule(rule, token.kind, token.attr, customize)
        elif opname == "CALL_FUNCTION_EX_KW":
            # Note: this doesn't exist in 3.7 and later
            self.addRule(
                """expr        ::= call_ex_kw4
                            call_ex_kw4 ::= expr
                                            expr
                                            expr
                                            CALL_FUNCTION_EX_KW
                         """,
                nop_func,
            )
            if "BUILD_MAP_UNPACK_WITH_CALL" in self.seen_op_basenames:
                self.addRule(
                    """expr        ::= call_ex_kw
                                call_ex_kw  ::= expr expr build_map_unpack_with_call
                                                CALL_FUNCTION_EX_KW
                             """,
                    nop_func,
                )
            if "BUILD_TUPLE_UNPACK_WITH_CALL" in self.seen_op_basenames:
                # FIXME: should this be parameterized by EX value?
                self.addRule(
                    """expr        ::= call_ex_kw3
                                call_ex_kw3 ::= expr
                                                build_tuple_unpack_with_call
                                                expr
                                                CALL_FUNCTION_EX_KW
                             """,
                    nop_func,
                )
                if "BUILD_MAP_UNPACK_WITH_CALL" in self.seen_op_basenames:
                    # FIXME: should this be parameterized by EX value?
                    self.addRule(
                        """expr        ::= call_ex_kw2
                                    call_ex_kw2 ::= expr
                                                    build_tuple_unpack_with_call
                                                    build_map_unpack_with_call
                                                    CALL_FUNCTION_EX_KW
                             """,
                        nop_func,
                    )

        elif opname == "CALL_FUNCTION_EX":
            self.addRule(
                """
                         expr        ::= call_ex
                         starred     ::= expr
                         call_ex     ::= expr starred CALL_FUNCTION_EX
                         """,
                nop_func,
            )
            if "BUILD_MAP_UNPACK_WITH_CALL" in self.seen_ops:
                self.addRule(
                    """
                        expr        ::= call_ex_kw
                        call_ex_kw  ::= expr expr
                                        build_map_unpack_with_call CALL_FUNCTION_EX
                        """,
                    nop_func,
                )
            if "BUILD_TUPLE_UNPACK_WITH_CALL" in self.seen_ops:
                self.addRule(
                    """
                        expr        ::= call_ex_kw3
                        call_ex_kw3 ::= expr
                                        build_tuple_unpack_with_call
                                        %s
                                        CALL_FUNCTION_EX
                        """
                    % "expr "
                    * token.attr,
                    nop_func,
                )
                pass

            # FIXME: Is this right?
            self.addRule(
                """
                        expr        ::= call_ex_kw4
                        call_ex_kw4 ::= expr
                                        expr
                                        expr
                                        CALL_FUNCTION_EX
                        """,
                nop_func,
            )
            pass
        else:
            super(Python37Parser, self).custom_classfunc_rule(
                opname, token, customize, next_token
            )

    def reduce_is_invalid(self, rule, ast, tokens, first, last):
        invalid = super(Python37Parser, self).reduce_is_invalid(
            rule, ast, tokens, first, last
        )
        if invalid:
            return invalid
        if rule[0] == "call_kw":
            # Make sure we don't derive call_kw
            nt = ast[0]
            while not isinstance(nt, Token):
                if nt[0] == "call_kw":
                    return True
                nt = nt[0]
                pass
            pass
        return False


def info(args):
    # Check grammar
    p = Python37Parser()
    if len(args) > 0:
        arg = args[0]
        if arg == "3.7":
            from uncompyle6.parser.parse37 import Python37Parser

            p = Python37Parser()
        elif arg == "3.8":
            from uncompyle6.parser.parse38 import Python38Parser

            p = Python38Parser()
        else:
            raise RuntimeError("Only 3.7 and 3.8 supported")
    p.check_grammar()
    if len(sys.argv) > 1 and sys.argv[1] == "dump":
        print("-" * 50)
        p.dump_grammar()


class Python37ParserSingle(Python37Parser, PythonParserSingle):
    pass


if __name__ == "__main__":
    # Check grammar
    # FIXME: DRY this with other parseXX.py routines
    p = Python37Parser()
    p.check_grammar()
    from xdis.version_info import IS_PYPY, PYTHON_VERSION_TRIPLE

    if PYTHON_VERSION_TRIPLE[:2] == (3, 7):
        lhs, rhs, tokens, right_recursive, dup_rhs = p.check_sets()
        from uncompyle6.scanner import get_scanner

        s = get_scanner(PYTHON_VERSION_TRIPLE, IS_PYPY)
        opcode_set = set(s.opc.opname).union(
            set(
                """JUMP_BACK CONTINUE RETURN_END_IF COME_FROM
               LOAD_GENEXPR LOAD_ASSERT LOAD_SETCOMP LOAD_DICTCOMP LOAD_CLASSNAME
               LAMBDA_MARKER RETURN_LAST
            """.split()
            )
        )
        remain_tokens = set(tokens) - opcode_set
        import re

        remain_tokens = set([re.sub(r"_\d+$", "", t) for t in remain_tokens])
        remain_tokens = set([re.sub("_CONT$", "", t) for t in remain_tokens])
        remain_tokens = set(remain_tokens) - opcode_set
        print(remain_tokens)
        import sys

        if len(sys.argv) > 1:
            from spark_parser.spark import rule2str

            for rule in sorted(p.rule2name.items()):
                print(rule2str(rule[0]))
