#  Copyright (c) 2016 Rocky Bernstein
#  Copyright (c) 2005 by Dan Pascu <dan@windowmaker.org>
#  Copyright (c) 2000-2002 by hartmut Goebel <hartmut@goebel.noris.de>
#  Copyright (c) 1999 John Aycock

import string
from spark_parser import GenericASTBuilder, DEFAULT_DEBUG as PARSER_DEFAULT_DEBUG
from uncompyle6.parsers.astnode import AST
from uncompyle6.parser import PythonParser, PythonParserSingle, nop_func

class Python23Parser(PythonParser):

    def __init__(self, debug_parser=PARSER_DEFAULT_DEBUG):
        super(Python23Parser, self).__init__(AST, 'stmts', debug=debug_parser)
        self.customized = {}

    # FIXME: A lot of the functions below overwrite what is in parse.py which
    # have more rules. Probly that should be stripped down more instead.

    def p_funcdef(self, args):
        '''
        stmt ::= funcdef
        funcdef ::= mkfunc designator
        load_closure ::= load_closure LOAD_CLOSURE
        load_closure ::= LOAD_CLOSURE
        '''

    def p_list_comprehension(self, args):
        '''
        expr ::= list_compr
        list_compr ::= BUILD_LIST_0 DUP_TOP _load_attr
                designator list_iter del_stmt

        list_iter ::= list_for
        list_iter ::= list_if
        list_iter ::= lc_body

        _load_attr ::= LOAD_ATTR
        _load_attr ::=

        _lcfor ::= GET_ITER LIST_COMPREHENSION_START FOR_ITER
        _lcfor ::= LOAD_CONST FOR_LOOP
        _lcfor2 ::= GET_ITER FOR_ITER
        _lcfor2 ::= LOAD_CONST FOR_LOOP

        list_for ::= expr _lcfor designator list_iter
                LIST_COMPREHENSION_END JUMP_ABSOLUTE

        list_for ::= expr _lcfor2 designator list_iter
                JUMP_ABSOLUTE

        list_if ::= expr condjmp IF_THEN_START list_iter
                IF_THEN_END _jump POP_TOP IF_ELSE_START IF_ELSE_END

        lc_body ::= LOAD_NAME expr CALL_FUNCTION_1 POP_TOP
        lc_body ::= LOAD_FAST expr CALL_FUNCTION_1 POP_TOP
        lc_body ::= LOAD_NAME expr LIST_APPEND
        lc_body ::= LOAD_FAST expr LIST_APPEND
        '''

    def p_augmented_assign(self, args):
        '''
        stmt ::= augassign1
        stmt ::= augassign2
        augassign1 ::= expr expr inplace_op designator
        augassign1 ::= expr expr inplace_op ROT_THREE STORE_SUBSCR
        augassign1 ::= expr expr inplace_op ROT_TWO   STORE_SLICE+0
        augassign1 ::= expr expr inplace_op ROT_THREE STORE_SLICE+1
        augassign1 ::= expr expr inplace_op ROT_THREE STORE_SLICE+2
        augassign1 ::= expr expr inplace_op ROT_FOUR  STORE_SLICE+3
        augassign2 ::= expr DUP_TOP LOAD_ATTR expr
                inplace_op ROT_TWO   STORE_ATTR

        inplace_op ::= INPLACE_ADD
        inplace_op ::= INPLACE_SUBTRACT
        inplace_op ::= INPLACE_MULTIPLY
        inplace_op ::= INPLACE_DIVIDE
        inplace_op ::= INPLACE_TRUE_DIVIDE
        inplace_op ::= INPLACE_FLOOR_DIVIDE
        inplace_op ::= INPLACE_MODULO
        inplace_op ::= INPLACE_POWER
        inplace_op ::= INPLACE_LSHIFT
        inplace_op ::= INPLACE_RSHIFT
        inplace_op ::= INPLACE_AND
        inplace_op ::= INPLACE_XOR
        inplace_op ::= INPLACE_OR
        '''

    def p_assign(self, args):
        '''
        stmt ::= assign
        assign ::= expr DUP_TOP designList
        assign ::= expr designator
        '''

    def p_print(self, args):
        '''
        stmt ::= print_stmt
        stmt ::= print_stmt_nl
        stmt ::= print_nl_stmt
        print_stmt ::= expr PRINT_ITEM
        print_nl_stmt ::= PRINT_NEWLINE
        print_stmt_nl ::= print_stmt print_nl_stmt
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
        # expr   print_to*   POP_TOP
        # expr { print_to* } PRINT_NEWLINE_TO

    def p_import15(self, args):
        '''
        stmt ::= importstmt
        stmt ::= importfrom

        importstmt ::= IMPORT_NAME STORE_FAST
        importstmt ::= IMPORT_NAME STORE_NAME

        importfrom ::= IMPORT_NAME importlist POP_TOP
        importlist ::= importlist IMPORT_FROM
        importlist ::= IMPORT_FROM
        '''

    # Python 2.0 - 2.3 imports
    def p_import20_23(self, args):
        '''
        stmt ::= importstmt20
        stmt ::= importfrom20
        stmt ::= importstar20

        importstmt20 ::= LOAD_CONST import_as
        importstar20 ::= LOAD_CONST IMPORT_NAME IMPORT_STAR

        importfrom20 ::= LOAD_CONST IMPORT_NAME importlist20 POP_TOP
        importlist20 ::= importlist20 import_as
        importlist20 ::= import_as
        import_as ::= IMPORT_NAME designator
        import_as ::= IMPORT_NAME LOAD_ATTR designator
        import_as ::= IMPORT_FROM designator
        '''

    def p_grammar(self, args):
        '''
        stmts ::= stmts stmt
        stmts ::= stmt

        stmts_opt ::= stmts
        stmts_opt ::= passstmt
        passstmt ::=

        stmt ::= classdef
        stmt ::= call_stmt
        call_stmt ::= expr POP_TOP

        stmt ::= return_stmt
        return_stmt ::= expr RETURN_VALUE

        stmt ::= yield_stmt
        yield_stmt ::= expr YIELD_STMT
        yield_stmt ::= expr YIELD_VALUE

        stmt ::= break_stmt
        break_stmt ::= BREAK_LOOP

        stmt ::= continue_stmt
        continue_stmt ::= JUMP_ABSOLUTE
        continue_stmt ::= CONTINUE_LOOP

        stmt ::= raise_stmt
        raise_stmt ::= exprlist RAISE_VARARGS
        raise_stmt ::= RAISE_VARARGS

        stmt ::= exec_stmt
        exec_stmt ::= expr exprlist DUP_TOP EXEC_STMT
        exec_stmt ::= expr exprlist EXEC_STMT

        stmt ::= assert
        stmt ::= assert2
        stmt ::= assert3
        stmt ::= assert4
        stmt ::= ifstmt
        stmt ::= ifelsestmt
        stmt ::= whilestmt
        stmt ::= while1stmt
        stmt ::= while12stmt
        stmt ::= whileelsestmt
        stmt ::= while1elsestmt
        stmt ::= while12elsestmt
        stmt ::= forstmt
        stmt ::= forelsestmt
        stmt ::= trystmt
        stmt ::= tryfinallystmt

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

        classdef ::= LOAD_CONST expr mkfunc
                    CALL_FUNCTION_0 BUILD_CLASS designator

        condjmp    ::= JUMP_IF_FALSE POP_TOP
        condjmp    ::= JUMP_IF_TRUE  POP_TOP

        assert ::= expr JUMP_IF_FALSE POP_TOP
                LOGIC_TEST_START expr JUMP_IF_TRUE POP_TOP
                LOGIC_TEST_START LOAD_GLOBAL RAISE_VARARGS
                LOGIC_TEST_END LOGIC_TEST_END POP_TOP
        assert2 ::= expr JUMP_IF_FALSE POP_TOP
                LOGIC_TEST_START expr JUMP_IF_TRUE POP_TOP
                LOGIC_TEST_START LOAD_GLOBAL expr RAISE_VARARGS
                LOGIC_TEST_END LOGIC_TEST_END POP_TOP
        assert3 ::= expr JUMP_IF_TRUE POP_TOP
                LOGIC_TEST_START LOAD_GLOBAL RAISE_VARARGS
                LOGIC_TEST_END POP_TOP
        assert4 ::= expr JUMP_IF_TRUE POP_TOP
                LOGIC_TEST_START LOAD_GLOBAL expr RAISE_VARARGS
                LOGIC_TEST_END POP_TOP

        _jump ::= JUMP_ABSOLUTE
        _jump ::= JUMP_FORWARD

        ifstmt ::= expr condjmp
                IF_THEN_START stmts_opt IF_THEN_END
                _jump POP_TOP IF_ELSE_START IF_ELSE_END

        ifelsestmt ::= expr condjmp
                IF_THEN_START stmts_opt IF_THEN_END
                _jump POP_TOP IF_ELSE_START stmts IF_ELSE_END

        trystmt ::= SETUP_EXCEPT TRY_START stmts_opt
                TRY_END POP_BLOCK _jump
                except_stmt

        try_end  ::= END_FINALLY TRY_ELSE_START TRY_ELSE_END
        try_end  ::= except_else
        except_else ::= END_FINALLY TRY_ELSE_START stmts TRY_ELSE_END

        except_stmt ::= except_stmt except_cond
        except_stmt ::= except_conds try_end
        except_stmt ::= except try_end
        except_stmt ::= try_end

        except_conds ::= except_conds except_cond
        except_conds ::=

        except_cond ::= except_cond1
        except_cond ::= except_cond2
        except_cond1 ::= EXCEPT_START DUP_TOP expr COMPARE_OP
                JUMP_IF_FALSE
                POP_TOP POP_TOP POP_TOP POP_TOP
                stmts_opt EXCEPT_END _jump POP_TOP
        except_cond2 ::= EXCEPT_START DUP_TOP expr COMPARE_OP
                JUMP_IF_FALSE
                POP_TOP POP_TOP designator POP_TOP
                stmts_opt EXCEPT_END _jump POP_TOP
        except ::= EXCEPT_START POP_TOP POP_TOP POP_TOP
                stmts_opt EXCEPT_END _jump

        tryfinallystmt ::= SETUP_FINALLY stmts_opt
                POP_BLOCK LOAD_CONST
                stmts_opt END_FINALLY

        _while1test ::= _jump JUMP_IF_FALSE POP_TOP
        _while1test ::=

        whilestmt ::= SETUP_LOOP WHILE_START
                expr condjmp
                stmts_opt WHILE_END JUMP_ABSOLUTE
                WHILE_ELSE_START POP_TOP POP_BLOCK WHILE_ELSE_END

        while1stmt ::= SETUP_LOOP _while1test WHILE1_START
                stmts_opt WHILE1_END JUMP_ABSOLUTE
                WHILE1_ELSE_START POP_TOP POP_BLOCK WHILE1_ELSE_END

        while12stmt ::= SETUP_LOOP WHILE1_START
                _jump JUMP_IF_FALSE POP_TOP
                stmts_opt WHILE1_END JUMP_ABSOLUTE
                WHILE1_ELSE_START POP_TOP POP_BLOCK WHILE1_ELSE_END

        whileelsestmt ::= SETUP_LOOP WHILE_START
                expr condjmp
                stmts_opt WHILE_END JUMP_ABSOLUTE
                WHILE_ELSE_START POP_TOP POP_BLOCK
                stmts WHILE_ELSE_END

        while1elsestmt ::= SETUP_LOOP _while1test WHILE1_START
                stmts_opt WHILE1_END JUMP_ABSOLUTE
                WHILE1_ELSE_START POP_TOP POP_BLOCK
                stmts WHILE1_ELSE_END

        while12elsestmt ::= SETUP_LOOP WHILE1_START
                _jump JUMP_IF_FALSE POP_TOP
                stmts_opt WHILE1_END JUMP_ABSOLUTE
                WHILE1_ELSE_START POP_TOP POP_BLOCK
                stmts WHILE1_ELSE_END

        _for ::= GET_ITER FOR_START FOR_ITER
        _for ::= LOAD_CONST FOR_LOOP

        forstmt ::= SETUP_LOOP expr _for designator
                stmts_opt FOR_END JUMP_ABSOLUTE
                FOR_ELSE_START POP_BLOCK FOR_ELSE_END
        forelsestmt ::= SETUP_LOOP expr _for designator
                stmts_opt FOR_END JUMP_ABSOLUTE
                FOR_ELSE_START POP_BLOCK stmts FOR_ELSE_END

        '''

    def p_expr(self, args):
        '''
        expr ::= load_closure mklambda
        expr ::= mklambda
        expr ::= SET_LINENO
        expr ::= LOAD_FAST
        expr ::= LOAD_NAME
        expr ::= LOAD_CONST
        expr ::= LOAD_GLOBAL
        expr ::= LOAD_DEREF
        expr ::= LOAD_LOCALS
        expr ::= expr LOAD_ATTR
        expr ::= binary_expr
        expr ::= build_list

        binary_expr ::= expr expr binary_op
        binary_op ::= BINARY_ADD
        binary_op ::= BINARY_SUBTRACT
        binary_op ::= BINARY_MULTIPLY
        binary_op ::= BINARY_DIVIDE
        binary_op ::= BINARY_TRUE_DIVIDE
        binary_op ::= BINARY_FLOOR_DIVIDE
        binary_op ::= BINARY_MODULO
        binary_op ::= BINARY_LSHIFT
        binary_op ::= BINARY_RSHIFT
        binary_op ::= BINARY_AND
        binary_op ::= BINARY_OR
        binary_op ::= BINARY_XOR
        binary_op ::= BINARY_POWER

        expr ::= binary_subscr
        binary_subscr ::= expr expr BINARY_SUBSCR
        expr ::= expr expr DUP_TOPX_2 BINARY_SUBSCR
        expr ::= cmp
        expr ::= expr UNARY_POSITIVE
        expr ::= expr UNARY_NEGATIVE
        expr ::= expr UNARY_CONVERT
        expr ::= expr UNARY_INVERT
        expr ::= expr UNARY_NOT
        expr ::= mapexpr
        expr ::= expr SLICE+0
        expr ::= expr expr SLICE+1
        expr ::= expr expr SLICE+2
        expr ::= expr expr expr SLICE+3
        expr ::= expr DUP_TOP SLICE+0
        expr ::= expr expr DUP_TOPX_2 SLICE+1
        expr ::= expr expr DUP_TOPX_2 SLICE+2
        expr ::= expr expr expr DUP_TOPX_3 SLICE+3
        expr ::= and
        expr ::= and2
        expr ::= or
        or   ::= expr JUMP_IF_TRUE  POP_TOP LOGIC_TEST_START expr LOGIC_TEST_END
        and  ::= expr JUMP_IF_FALSE POP_TOP LOGIC_TEST_START expr LOGIC_TEST_END
        and2 ::= _jump JUMP_IF_FALSE POP_TOP LOGIC_TEST_START expr LOGIC_TEST_END

        cmp ::= cmp_list
        cmp ::= compare
        compare ::= expr expr COMPARE_OP
        cmp_list ::= expr cmp_list1 ROT_TWO IF_ELSE_START POP_TOP
                IF_ELSE_END
        cmp_list1 ::= expr DUP_TOP ROT_THREE
                COMPARE_OP JUMP_IF_FALSE POP_TOP
                cmp_list1
        cmp_list1 ::= expr DUP_TOP ROT_THREE
                COMPARE_OP JUMP_IF_FALSE POP_TOP
                IF_THEN_START cmp_list1
        cmp_list1 ::= expr DUP_TOP ROT_THREE
                COMPARE_OP JUMP_IF_FALSE POP_TOP
                IF_THEN_START cmp_list2
        cmp_list1 ::= expr DUP_TOP ROT_THREE
                COMPARE_OP JUMP_IF_FALSE POP_TOP
                cmp_list2
        cmp_list2 ::= expr COMPARE_OP IF_THEN_END JUMP_FORWARD
        mapexpr ::= BUILD_MAP kvlist

        kvlist ::= kvlist kv
        kvlist ::= kvlist kv2
        kvlist ::=

        kv ::= DUP_TOP expr ROT_TWO expr STORE_SUBSCR
        kv2 ::= DUP_TOP expr expr ROT_THREE STORE_SUBSCR

        exprlist ::= exprlist expr
        exprlist ::= expr
        '''

    def nonterminal(self, nt, args):
        collect = ('stmts', 'exprlist', 'kvlist')

        if nt in collect and len(args) > 1:
            #
            #  Collect iterated thingies together.
            #
            rv = args[0]
            rv.append(args[1])
        else:
            rv = GenericASTBuilder.nonterminal(self, nt, args)
        return rv

    def __ambiguity(self, children):
        # only for debugging! to be removed hG/2000-10-15
        print children
        return GenericASTBuilder.ambiguity(self, children)

    def resolve(self, list):
        if len(list) == 2 and 'funcdef' in list and 'assign' in list:
            return 'funcdef'
        #print >> sys.stderr, 'resolve', str(list)
        return GenericASTBuilder.resolve(self, list)

    def add_custom_rules(self, tokens, customize):
        """
         Special handling for opcodes that take a variable number
         of arguments -- we add a new rule for each:

            expr ::= {expr}^n BUILD_LIST_n
            expr ::= {expr}^n BUILD_TUPLE_n
            expr ::= {expr}^n BUILD_SLICE_n
            unpack_list ::= UNPACK_LIST {expr}^n
            unpack ::= UNPACK_TUPLE {expr}^n
            unpack ::= UNPACK_SEQEUENE {expr}^n
            mkfunc ::= {expr}^n LOAD_CONST MAKE_FUNCTION_n
            mkfunc ::= {expr}^n load_closure LOAD_CONST MAKE_FUNCTION_n
            expr ::= expr {expr}^n CALL_FUNCTION_n
            expr ::= expr {expr}^n CALL_FUNCTION_VAR_n POP_TOP
            expr ::= expr {expr}^n CALL_FUNCTION_VAR_KW_n POP_TOP
            expr ::= expr {expr}^n CALL_FUNCTION_KW_n POP_TOP
        """
        for k, v in customize.items():
            # avoid adding the same rule twice to this parser
            if self.customized.has_key(k):
                continue
            self.customized[k] = None

            #nop_func = lambda self, args: None
            op = k[:string.rfind(k, '_')]
            if op in ('BUILD_LIST', 'BUILD_TUPLE'):
                rule = 'build_list ::= ' + 'expr '*v + k
            elif op == 'BUILD_SLICE':
                rule = 'expr ::= ' + 'expr '*v + k
            elif op in ('UNPACK_TUPLE', 'UNPACK_SEQUENCE'):
                rule = 'unpack ::= ' + k + ' designator'*v
            elif op == 'UNPACK_LIST':
                rule = 'unpack_list ::= ' + k + ' designator'*v
            elif op == 'DUP_TOPX':
                # no need to add a rule
                continue
                #rule = 'dup_topx ::= ' + 'expr '*v + k
            elif op == 'MAKE_FUNCTION':
                self.addRule('mklambda ::= %s LOAD_LAMBDA %s' %
                      ('expr '*v, k), nop_func)
                rule = 'mkfunc ::= %s LOAD_CONST %s' % ('expr '*v, k)
            elif op == 'MAKE_CLOSURE':
                self.addRule('mklambda ::= %s load_closure LOAD_LAMBDA %s' %
                      ('expr '*v, k), nop_func)
                rule = 'mkfunc ::= %s load_closure LOAD_CONST %s' % ('expr '*v, k)
            elif op in ('CALL_FUNCTION', 'CALL_FUNCTION_VAR',
                    'CALL_FUNCTION_VAR_KW', 'CALL_FUNCTION_KW'):
                na = (v & 0xff)           # positional parameters
                nk = (v >> 8) & 0xff      # keyword parameters
                # number of apply equiv arguments:
                nak = ( len(op)-len('CALL_FUNCTION') ) / 3
                rule = 'expr ::= expr ' + 'expr '*na + 'kwarg '*nk \
                       + 'expr ' * nak + k
            else:
                raise 'unknown customize token %s' % k
            self.addRule(rule, nop_func)
        return
    pass


class Python23ParserSingle(Python23Parser, PythonParserSingle):
    pass

if __name__ == '__main__':
    # Check grammar
    p = Python23Parser()
    p.checkGrammar()

# local variables:
# tab-width: 4
