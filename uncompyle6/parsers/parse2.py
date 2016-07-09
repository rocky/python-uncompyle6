#  Copyright (c) 2015-2016 Rocky Bernstein
#  Copyright (c) 2000-2002 by hartmut Goebel <h.goebel@crazy-compilers.com>
#  Copyright (c) 1999 John Aycock
"""
A spark grammar for Python 2.x.

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

class Python2Parser(PythonParser):

    def __init__(self, debug_parser=PARSER_DEFAULT_DEBUG):
        super(Python2Parser, self).__init__(AST, 'stmts', debug=debug_parser)
        self.new_rules = set()

    def p_print2(self, args):
        '''
        stmt ::= print_items_stmt
        stmt ::= print_nl
        stmt ::= print_items_nl_stmt

        print_items_stmt ::= expr PRINT_ITEM print_items_opt
        print_items_nl_stmt ::= expr PRINT_ITEM print_items_opt PRINT_NEWLINE_CONT
        print_items_opt ::= print_items
        print_items_opt ::=
        print_items ::= print_items print_item
        print_items ::= print_item
        print_item ::= expr PRINT_ITEM_CONT
        print_nl ::= PRINT_NEWLINE
        '''

    def p_print_to(self, args):
        '''
        stmt ::= print_to
        stmt ::= print_to_nl
        stmt ::= print_nl_to
        print_to ::= expr print_to_items POP_TOP
        print_to_nl ::= expr print_to_items PRINT_NEWLINE_TO
        print_nl_to ::= expr PRINT_NEWLINE_TO
        print_to_items ::= print_to_items print_to_item
        print_to_items ::= print_to_item
        print_to_item ::= DUP_TOP expr ROT_TWO PRINT_ITEM_TO
        '''

    def p_grammar(self, args):
        '''
        sstmt ::= stmt
        sstmt ::= ifelsestmtr
        sstmt ::= return_stmt RETURN_LAST

        return_if_stmts ::= return_if_stmt
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

        classdef ::= buildclass designator

        buildclass ::= LOAD_CONST expr mkfunc
                     CALL_FUNCTION_0 BUILD_CLASS

        stmt ::= classdefdeco
        classdefdeco ::= classdefdeco1 designator
        classdefdeco1 ::= expr classdefdeco1 CALL_FUNCTION_1
        classdefdeco1 ::= expr classdefdeco2 CALL_FUNCTION_1
        classdefdeco2 ::= LOAD_CONST expr mkfunc CALL_FUNCTION_0 BUILD_CLASS

        assert2 ::= assert_expr jmp_true LOAD_ASSERT expr CALL_FUNCTION_1 RAISE_VARARGS_1

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

        iflaststmt ::= testexpr c_stmts_opt JUMP_ABSOLUTE

        iflaststmtl ::= testexpr c_stmts_opt JUMP_BACK

        ifelsestmt ::= testexpr c_stmts_opt JUMP_FORWARD else_suite COME_FROM

        ifelsestmtc ::= testexpr c_stmts_opt JUMP_ABSOLUTE else_suitec

        ifelsestmtr ::= testexpr return_if_stmts return_stmts

        ifelsestmtl ::= testexpr c_stmts_opt JUMP_BACK else_suitel


        # this is nested inside a trystmt
        tryfinallystmt ::= SETUP_FINALLY suite_stmts_opt
                           POP_BLOCK LOAD_CONST
                           COME_FROM suite_stmts_opt END_FINALLY

        # Move to 2.7? 2.6 may use come_froms
        tryelsestmtc ::= SETUP_EXCEPT suite_stmts_opt POP_BLOCK
                         try_middle else_suitec COME_FROM

        tryelsestmtl ::= SETUP_EXCEPT suite_stmts_opt POP_BLOCK
                         try_middle else_suitel COME_FROM

        trystmt      ::= SETUP_EXCEPT suite_stmts_opt POP_BLOCK
                         try_middle COME_FROM

        except_stmts ::= except_stmts except_stmt
        except_stmts ::= except_stmt

        except_stmt ::= except_cond1 except_suite
        except_stmt ::= except_cond2 except_suite
        except_stmt ::= except

        except_suite ::= c_stmts_opt JUMP_FORWARD
        except_suite ::= c_stmts_opt jmp_abs
        except_suite ::= return_stmts

        except  ::=  POP_TOP POP_TOP POP_TOP c_stmts_opt _jump
        except  ::=  POP_TOP POP_TOP POP_TOP return_stmts

        jmp_abs ::= JUMP_ABSOLUTE
        jmp_abs ::= JUMP_BACK
        '''

    def p_dictcomp2(self, args):
        """"
        dictcomp ::= LOAD_DICTCOMP MAKE_FUNCTION_0 expr GET_ITER CALL_FUNCTION_1
        """

    def p_genexpr2(self, args):
        '''
        genexpr ::= LOAD_GENEXPR MAKE_FUNCTION_0 expr GET_ITER CALL_FUNCTION_1
        '''

    def p_expr2(self, args):
        '''
        expr ::= LOAD_LOCALS

        slice0 ::= expr SLICE+0
        slice0 ::= expr DUP_TOP SLICE+0
        slice1 ::= expr expr SLICE+1
        slice1 ::= expr expr DUP_TOPX_2 SLICE+1
        slice2 ::= expr expr SLICE+2
        slice2 ::= expr expr DUP_TOPX_2 SLICE+2
        slice3 ::= expr expr expr SLICE+3
        slice3 ::= expr expr expr DUP_TOPX_3 SLICE+3

        # In Python 3, DUP_TOPX_2 is DUP_TOP_TWO
        binary_subscr2 ::= expr expr DUP_TOPX_2 BINARY_SUBSCR
        '''

    def add_custom_rules(self, tokens, customize):
        '''
        Special handling for opcodes that take a variable number
        of arguments -- we add a new rule for each:

            build_list  ::= {expr}^n BUILD_LIST_n
            build_list  ::= {expr}^n BUILD_TUPLE_n
            unpack_list ::= UNPACK_LIST {expr}^n
            unpack      ::= UNPACK_TUPLE {expr}^n
            unpack      ::= UNPACK_SEQEUENCE {expr}^n

            mkfunc      ::= {expr}^n LOAD_CONST MAKE_FUNCTION_n
            mklambda    ::= {expr}^n LOAD_LAMBDA MAKE_FUNCTION_n
            mkfunc      ::= {expr}^n load_closure LOAD_CONST MAKE_FUNCTION_n
            expr ::= expr {expr}^n CALL_FUNCTION_n
            expr ::= expr {expr}^n CALL_FUNCTION_VAR_n POP_TOP
            expr ::= expr {expr}^n CALL_FUNCTION_VAR_KW_n POP_TOP
            expr ::= expr {expr}^n CALL_FUNCTION_KW_n POP_TOP
        '''
        for k, v in list(customize.items()):
            op = k[:k.rfind('_')]
            if op in ('BUILD_LIST', 'BUILD_TUPLE', 'BUILD_SET'):
                thousands = (v//1024)
                thirty32s = ((v//32)%32)
                if thirty32s > 0:
                    rule = "expr32 ::=%s" % (' expr' * 32)
                    self.add_unique_rule(rule, op, v, customize)
                    self.seen32 = True
                if thousands > 0:
                    self.add_unique_rule("expr1024 ::=%s" % (' expr32' * 32),
                                         op, v, customize)
                    self.seen1024 = True
                rule = ('build_list ::= ' + 'expr1024 '*thousands +
                                        'expr32 '*thirty32s + 'expr '*(v%32) + k)
            elif op == 'BUILD_MAP':
                kvlist_n = "kvlist_%s" % v
                rule = kvlist_n + ' ::= ' + ' kv3' * v
                self.add_unique_rule(rule, op, v, customize)
                rule = "mapexpr ::=  %s %s" % (k, kvlist_n)
                self.add_unique_rule(rule, op, v, customize)
            elif op in ('UNPACK_TUPLE', 'UNPACK_SEQUENCE'):
                rule = 'unpack ::= ' + k + ' designator'*v
            elif op == 'UNPACK_LIST':
                rule = 'unpack_list ::= ' + k + ' designator'*v
            elif op in ('DUP_TOPX', 'RAISE_VARARGS'):
                # no need to add a rule
                continue
                # rule = 'dup_topx ::= ' + 'expr '*v + k
            elif op == 'MAKE_FUNCTION':
                self.addRule('mklambda ::= %s LOAD_LAMBDA %s' %
                      ('pos_arg '*v, k), nop_func)
                rule = 'mkfunc ::= %s LOAD_CONST %s' % ('expr '*v, k)
            elif op == 'MAKE_CLOSURE':
                self.addRule('mklambda ::= %s load_closure LOAD_LAMBDA %s' %
                      ('expr '*v, k), nop_func)
                self.addRule('genexpr ::= %s load_closure LOAD_GENEXPR %s expr GET_ITER CALL_FUNCTION_1' %
                      ('expr '*v, k), nop_func)
                self.addRule('setcomp ::= %s load_closure LOAD_SETCOMP %s expr GET_ITER CALL_FUNCTION_1' %
                      ('expr '*v, k), nop_func)
                self.addRule('dictcomp ::= %s load_closure LOAD_DICTCOMP %s expr GET_ITER CALL_FUNCTION_1' %
                      ('expr '*v, k), nop_func)
                rule = 'mkfunc ::= %s load_closure LOAD_CONST %s' % ('expr '*v, k)
                # rule = 'mkfunc ::= %s closure_list LOAD_CONST %s' % ('expr '*v, k)
            elif op in ('CALL_FUNCTION', 'CALL_FUNCTION_VAR',
                    'CALL_FUNCTION_VAR_KW', 'CALL_FUNCTION_KW'):
                na = (v & 0xff)           # positional parameters
                nk = (v >> 8) & 0xff      # keyword parameters
                # number of apply equiv arguments:
                nak = ( len(op)-len('CALL_FUNCTION') ) // 3
                rule = 'call_function ::= expr ' + 'expr '*na + 'kwarg '*nk \
                       + 'expr ' * nak + k
            else:
                raise Exception('unknown customize token %s' % k)
            self.add_unique_rule(rule, op, v, customize)

class Python2ParserSingle(Python2Parser, PythonParserSingle):
    pass

if __name__ == '__main__':
    # Check grammar
    p = Python2Parser()
    p.checkGrammar()
