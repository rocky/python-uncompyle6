#  Copyright (c) 2015-2017 Rocky Bernstein
#  Copyright (c) 2000-2002 by hartmut Goebel <h.goebel@crazy-compilers.com>
#  Copyright (c) 1999 John Aycock
"""
A spark grammar for Python 2.x.

However instead of terminal symbols being the usual ASCII text,
e.g. 5, myvariable, "for", etc.  they are CPython Bytecode tokens,
e.g. "LOAD_CONST 5", "STORE NAME myvariable", "SETUP_LOOP", etc.

If we succeed in creating a parse tree, then we have a Python program
that a later phase can turn into a sequence of ASCII text.
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
        """
        stmt ::= print_items_stmt
        stmt ::= print_nl
        stmt ::= print_items_nl_stmt

        print_items_stmt ::= expr PRINT_ITEM print_items_opt
        print_items_nl_stmt ::= expr PRINT_ITEM print_items_opt PRINT_NEWLINE_CONT
        print_items_opt ::= print_items?
        print_items     ::= print_item+
        print_item      ::= expr PRINT_ITEM_CONT
        print_nl        ::= PRINT_NEWLINE
        """

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
        sstmt ::= return RETURN_LAST

        return_if_stmts ::= return_if_stmt
        return_if_stmts ::= _stmts return_if_stmt
        return_if_stmt ::= ret_expr RETURN_END_IF

        return_stmt_lambda ::= ret_expr RETURN_VALUE_LAMBDA

        stmt      ::= break
        break     ::= BREAK_LOOP

        stmt      ::= continue
        continue  ::= CONTINUE
        continues ::= _stmts lastl_stmt continue
        continues ::= lastl_stmt continue
        continues ::= continue

        stmt ::= assert2
        stmt ::= raise_stmt0
        stmt ::= raise_stmt1
        stmt ::= raise_stmt2
        stmt ::= raise_stmt3

        raise_stmt0 ::= RAISE_VARARGS_0
        raise_stmt1 ::= expr RAISE_VARARGS_1
        raise_stmt2 ::= expr expr RAISE_VARARGS_2
        raise_stmt3 ::= expr expr expr RAISE_VARARGS_3

        del_stmt ::= expr DELETE_SLICE+0
        del_stmt ::= expr expr DELETE_SLICE+1
        del_stmt ::= expr expr DELETE_SLICE+2
        del_stmt ::= expr expr expr DELETE_SLICE+3
        del_stmt ::= delete_subscr
        delete_subscr ::= expr expr DELETE_SUBSCR
        del_stmt ::= expr DELETE_ATTR

        _mklambda ::= load_closure mklambda
        kwarg     ::= LOAD_CONST expr

        kvlist ::= kvlist kv3
        kv3 ::= expr expr STORE_MAP

        dict ::= BUILD_MAP kvlist

        classdef ::= buildclass store

        buildclass ::= LOAD_CONST expr mkfunc
                     CALL_FUNCTION_0 BUILD_CLASS

        # Class decorators starting in 2.6
        stmt ::= classdefdeco
        classdefdeco ::= classdefdeco1 store
        classdefdeco1 ::= expr classdefdeco1 CALL_FUNCTION_1
        classdefdeco1 ::= expr classdefdeco2 CALL_FUNCTION_1
        classdefdeco2 ::= LOAD_CONST expr mkfunc CALL_FUNCTION_0 BUILD_CLASS

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

        iflaststmt  ::= testexpr c_stmts_opt JUMP_ABSOLUTE
        iflaststmtl ::= testexpr c_stmts_opt JUMP_BACK

        # this is nested inside a try_except
        tryfinallystmt  ::= SETUP_FINALLY suite_stmts_opt
                            POP_BLOCK LOAD_CONST
                            COME_FROM suite_stmts_opt END_FINALLY

        lastc_stmt ::= tryelsestmtc

        # Move to 2.7? 2.6 may use come_froms
        tryelsestmtc    ::= SETUP_EXCEPT suite_stmts_opt POP_BLOCK
                            except_handler else_suitec COME_FROM

        tryelsestmtl    ::= SETUP_EXCEPT suite_stmts_opt POP_BLOCK
                            except_handler else_suitel COME_FROM

        try_except      ::= SETUP_EXCEPT suite_stmts_opt POP_BLOCK
                            except_handler COME_FROM

        except_handler  ::= JUMP_FORWARD COME_FROM except_stmts
                            END_FINALLY COME_FROM
        except_handler  ::= jmp_abs COME_FROM except_stmts
                             END_FINALLY

        except_stmts ::= except_stmt+

        except_stmt ::= except_cond1 except_suite
        except_stmt ::= except

        except_suite ::= c_stmts_opt JUMP_FORWARD
        except_suite ::= c_stmts_opt jmp_abs
        except_suite ::= returns

        except  ::=  POP_TOP POP_TOP POP_TOP c_stmts_opt _jump
        except  ::=  POP_TOP POP_TOP POP_TOP returns

        jmp_abs ::= JUMP_ABSOLUTE
        jmp_abs ::= JUMP_BACK
        jmp_abs ::= CONTINUE
        '''

    def p_generator_exp2(self, args):
        '''
        generator_exp ::= LOAD_GENEXPR MAKE_FUNCTION_0 expr GET_ITER CALL_FUNCTION_1
        '''

    def p_expr2(self, args):
        """
        expr ::= LOAD_LOCALS
        expr ::= slice0
        expr ::= slice1
        expr ::= slice2
        expr ::= slice3
        expr ::= unary_convert

        and  ::= expr jmp_false expr come_from_opt
        or   ::= expr jmp_true  expr come_from_opt

        unary_convert ::= expr UNARY_CONVERT

        # In Python 3, DUP_TOPX_2 is DUP_TOP_TWO
        subscript2 ::= expr expr DUP_TOPX_2 BINARY_SUBSCR
        """

    def p_slice2(self, args):
        """
        store ::= expr STORE_SLICE+0
        store ::= expr expr STORE_SLICE+1
        store ::= expr expr STORE_SLICE+2
        store ::= expr expr expr STORE_SLICE+3

        aug_assign1 ::= expr expr inplace_op ROT_FOUR  STORE_SLICE+3
        aug_assign1 ::= expr expr inplace_op ROT_THREE STORE_SLICE+1
        aug_assign1 ::= expr expr inplace_op ROT_THREE STORE_SLICE+2
        aug_assign1 ::= expr expr inplace_op ROT_TWO   STORE_SLICE+0

        slice0 ::= expr SLICE+0
        slice0 ::= expr DUP_TOP SLICE+0
        slice1 ::= expr expr SLICE+1
        slice1 ::= expr expr DUP_TOPX_2 SLICE+1
        slice2 ::= expr expr SLICE+2
        slice2 ::= expr expr DUP_TOPX_2 SLICE+2
        slice3 ::= expr expr expr SLICE+3
        slice3 ::= expr expr expr DUP_TOPX_3 SLICE+3
        """

    def p_op2(self, args):
        """
        inplace_op ::= INPLACE_DIVIDE
        binary_op  ::= BINARY_DIVIDE
        """

    def customize_grammar_rules(self, tokens, customize):
        """The base grammar we start out for a Python version even with the
        subclassing is, well, is pretty base.  And we want it that way: lean and
        mean so that parsing will go faster.

        Here, we add additional grammar rules based on specific instructions
        that are in the instruction/token stream. In classes that
        inherit from from here and other versions, grammar rules may
        also be removed.

        For example if we see a pretty rare JUMP_IF_NOT_DEBUG
        instruction we'll add the grammar for that.

        More importantly, here we add grammar rules for instructions
        that may access a variable number of stack items. CALL_FUNCTION,
        BUILD_LIST and so on are like this.

        Without custom rules, there can be an super-exponential number of
        derivations. See the deparsing paper for an elaboration of
        this.
        """

        if 'PyPy' in customize:
            # PyPy-specific customizations
            self.addRule("""
                        stmt ::= assign3_pypy
                        stmt ::= assign2_pypy
                        assign3_pypy ::= expr expr expr store store store
                        assign2_pypy ::= expr expr store store
                        list_comp    ::= expr  BUILD_LIST_FROM_ARG for_iter store list_iter
                                         JUMP_BACK
                        """, nop_func)

        # For a rough break out on the first word. This may
        # include instructions that don't need customization,
        # but we'll do a finer check after the rough breakout.
        customize_instruction_basenames = frozenset(
            ('BUILD',     'CALL',       'CONTINUE',  'DELETE',
             'DUP',       'EXEC',       'GET',       'JUMP',
             'LOAD',      'LOOKUP',     'MAKE',      'SETUP',
             'RAISE',     'UNPACK'))

        # Opcode names in the custom_ops_seen set have rules that get added
        # unconditionally and the rules are constant. So they need to be done
        # only once and if we see the opcode a second we don't have to consider
        # adding more rules.
        #
        custom_ops_seen = set()

        for i, token in enumerate(tokens):
            opname = token.kind

            # Do a quick breakout before testing potentially
            # each of the dozen or so instruction in if elif.
            if (opname[:opname.find('_')] not in customize_instruction_basenames
                    or opname in custom_ops_seen):
                continue

            opname_base = opname[:opname.rfind('_')]

            # The order of opname listed is roughly sorted below
            if opname_base in ('BUILD_LIST', 'BUILD_SET', 'BUILD_TUPLE'):
                v = token.attr
                thousands = (v//1024)
                thirty32s = ((v//32) % 32)
                if thirty32s > 0:
                    rule = "expr32 ::=%s" % (' expr' * 32)
                    self.add_unique_rule(rule, opname_base, v, customize)
                    self.seen32 = True
                if thousands > 0:
                    self.add_unique_rule("expr1024 ::=%s" % (' expr32' * 32),
                                         opname_base, v, customize)
                    self.seen1024 = True
                collection = opname_base[opname_base.find('_')+1:].lower()
                rule = (('%s ::= ' % collection) + 'expr1024 '*thousands +
                        'expr32 '*thirty32s + 'expr '*(v % 32) + opname)
                self.add_unique_rules([
                    "expr ::= %s" % collection,
                    rule], customize)
                continue
            elif opname_base == 'BUILD_MAP':
                if opname == 'BUILD_MAP_n':
                    # PyPy sometimes has no count. Sigh.
                    self.add_unique_rules([
                        'kvlist_n ::=  kvlist_n kv3',
                        'kvlist_n ::=',
                        'dict ::= BUILD_MAP_n kvlist_n',
                    ], customize)
                    if self.version >= 2.7:
                        self.add_unique_rule(
                            'dict_comp_func ::= BUILD_MAP_n LOAD_FAST FOR_ITER store '
                            'comp_iter JUMP_BACK RETURN_VALUE RETURN_LAST',
                            'dict_comp_func', 0, customize)

                else:
                    kvlist_n = "kvlist_%s" % token.attr
                    self.add_unique_rules([
                        (kvlist_n + " ::=" + ' kv3' * token.attr),
                        "dict ::= %s %s" % (opname, kvlist_n)
                    ], customize)
                continue
            elif opname_base == 'BUILD_SLICE':
                slice_num  = token.attr
                if slice_num == 2:
                     self.add_unique_rules([
                        'expr ::= build_slice2',
                        'build_slice2 ::= expr expr BUILD_SLICE_2'
                        ], customize)
                else:
                    assert slice_num == 3, ("BUILD_SLICE value must be 2 or 3; is %s" %
                                            slice_num)
                    self.add_unique_rules([
                        'expr ::= build_slice3',
                        'build_slice3 ::= expr expr expr BUILD_SLICE_3',
                        ], customize)
                continue
            elif opname_base in ('CALL_FUNCTION', 'CALL_FUNCTION_VAR',
                                 'CALL_FUNCTION_VAR_KW', 'CALL_FUNCTION_KW'):

                args_pos, args_kw = self.get_pos_kw(token)

                # number of apply equiv arguments:
                nak = ( len(opname_base)-len('CALL_FUNCTION') ) // 3
                rule = 'call ::= expr ' + 'expr '*args_pos + 'kwarg '*args_kw \
                       + 'expr ' * nak + opname
            elif opname_base == 'CALL_METHOD':
                # PyPy only - DRY with parse3

                args_pos, args_kw = self.get_pos_kw(token)

                # number of apply equiv arguments:
                nak = ( len(opname_base)-len('CALL_METHOD') ) // 3
                rule = 'call ::= expr ' + 'expr '*args_pos + 'kwarg '*args_kw \
                       + 'expr ' * nak + opname
            elif opname == 'CONTINUE_LOOP':
                self.addRule('continue ::= CONTINUE_LOOP', nop_func)
                custom_ops_seen.add(opname)
                continue
            elif opname == 'DELETE_ATTR':
                self.addRule('del_stmt ::= expr DELETE_ATTR', nop_func)
                custom_ops_seen.add(opname)
                continue
            elif opname == 'DELETE_DEREF':
                self.addRule("""
                   stmt           ::= del_deref_stmt
                   del_deref_stmt ::= DELETE_DEREF
                   """, nop_func)
                custom_ops_seen.add(opname)
                continue
            elif opname == 'DELETE_SUBSCR':
                self.addRule("""
                    del_stmt ::= delete_subscr
                    delete_subscr ::= expr expr DELETE_SUBSCR
                   """, nop_func)
                custom_ops_seen.add(opname)
                continue
            elif opname == 'GET_ITER':
                self.addRule("""
                    expr      ::= get_iter
                    attribute ::= expr GET_ITER
                    """, nop_func)
                custom_ops_seen.add(opname)
                continue
            elif opname_base in ('DUP_TOPX', 'RAISE_VARARGS'):
                # FIXME: remove these conditions if they are not needed.
                # no longer need to add a rule
                continue
            elif opname == 'EXEC_STMT':
                self.addRule("""
                    stmt      ::= exec_stmt
                    exec_stmt ::= expr exprlist DUP_TOP EXEC_STMT
                    exec_stmt ::= expr exprlist EXEC_STMT
                    exprlist  ::= expr+
                    """, nop_func)
                continue
            elif opname == 'JUMP_IF_NOT_DEBUG':
                v = token.attr
                self.addRule("""
                    jmp_true_false ::= POP_JUMP_IF_TRUE
                    jmp_true_false ::= POP_JUMP_IF_FALSE
                    stmt ::= assert_pypy
                    stmt ::= assert2_pypy
                    assert_pypy  ::= JUMP_IF_NOT_DEBUG assert_expr jmp_true_false
                                     LOAD_ASSERT RAISE_VARARGS_1 COME_FROM
                    assert2_pypy ::= JUMP_IF_NOT_DEBUG assert_expr jmp_true_false
                                     LOAD_ASSERT expr CALL_FUNCTION_1
                                     RAISE_VARARGS_1 COME_FROM
                     """, nop_func)
                continue
            elif opname == 'LOAD_ATTR':
                self.addRule("""
                  expr      ::= attribute
                  attribute ::= expr LOAD_ATTR
                  """, nop_func)
                custom_ops_seen.add(opname)
                continue
            elif opname == 'LOAD_LISTCOMP':
                self.addRule("expr ::= listcomp", nop_func)
                custom_ops_seen.add(opname)
                continue
            elif opname == 'LOAD_SETCOMP':
                self.add_unique_rules([
                    "expr ::= set_comp",
                    "set_comp ::= LOAD_SETCOMP MAKE_FUNCTION_0 expr GET_ITER CALL_FUNCTION_1"
                    ], customize)
                custom_ops_seen.add(opname)
                continue
            elif opname == 'LOOKUP_METHOD':
                # A PyPy speciality - DRY with parse3
                self.addRule("""
                             expr      ::= attribute
                             attribute ::= expr LOOKUP_METHOD
                             """,
                             nop_func)
                custom_ops_seen.add(opname)
                continue
            elif opname_base == 'MAKE_FUNCTION':
                if i > 0 and tokens[i-1] == 'LOAD_LAMBDA':
                    self.addRule('mklambda ::= %s LOAD_LAMBDA %s' %
                                 ('pos_arg ' * token.attr, opname), nop_func)
                rule = 'mkfunc ::= %s LOAD_CONST %s' % ('expr ' * token.attr, opname)
            elif opname_base == 'MAKE_CLOSURE':
                # FIXME: use add_unique_rules to tidy this up.
                if i > 0 and tokens[i-1] == 'LOAD_LAMBDA':
                    self.addRule('mklambda ::= %s load_closure LOAD_LAMBDA %s' %
                                 ('expr ' * token.attr, opname),  nop_func)
                if i > 0:
                    prev_tok = tokens[i-1]
                    if prev_tok == 'LOAD_GENEXPR':
                        self.add_unique_rules([
                            ('generator_exp ::= %s load_closure LOAD_GENEXPR %s expr'
                                 ' GET_ITER CALL_FUNCTION_1' %
                            ('expr ' * token.attr, opname))], customize)
                        pass
                self.add_unique_rules([
                    ('mkfunc ::= %s load_closure LOAD_CONST %s' %
                     ('expr '* token.attr, opname))], customize)

                if self.version >= 2.7:
                    if i > 0:
                        prev_tok = tokens[i-1]
                        if prev_tok == 'LOAD_DICTCOMP':
                            self.add_unique_rules([
                                ('dict_comp ::= %s load_closure LOAD_DICTCOMP %s expr'
                                 ' GET_ITER CALL_FUNCTION_1' %
                                ('expr ' * token.attr, opname))], customize)
                        elif prev_tok == 'LOAD_SETCOMP':
                            self.add_unique_rules([
                                "expr ::= set_comp",
                                ('set_comp ::= %s load_closure LOAD_SETCOMP %s expr'
                                ' GET_ITER CALL_FUNCTION_1' %
                                ('expr ' * token.attr, opname))
                                ], customize)
                        pass
                    pass
                continue
            elif opname == 'SETUP_EXCEPT':
                if 'PyPy' in customize:
                    self.add_unique_rules([
                        "stmt ::= try_except_pypy",
                        "try_except_pypy ::= SETUP_EXCEPT suite_stmts_opt except_handler_pypy",
                        "except_handler_pypy ::= COME_FROM except_stmts END_FINALLY COME_FROM"
                        ], customize)
                custom_ops_seen.add(opname)
                continue
            elif opname == 'SETUP_FINALLY':
                if 'PyPy' in customize:
                    self.addRule("""
                        stmt ::= tryfinallystmt_pypy
                        tryfinallystmt_pypy ::= SETUP_FINALLY suite_stmts_opt COME_FROM_FINALLY
                                                suite_stmts_opt END_FINALLY""", nop_func)

                custom_ops_seen.add(opname)
                continue
            elif opname_base in ('UNPACK_TUPLE', 'UNPACK_SEQUENCE'):
                custom_ops_seen.add(opname)
                rule = 'unpack ::= ' + opname + ' store' * token.attr
            elif opname_base == 'UNPACK_LIST':
                custom_ops_seen.add(opname)
                rule = 'unpack_list ::= ' + opname + ' store' * token.attr
            else:
                continue
            self.addRule(rule, nop_func)
            pass

        self.check_reduce['aug_assign1'] = 'AST'
        self.check_reduce['aug_assign2'] = 'AST'
        # self.check_reduce['_stmts'] = 'AST'

        # Dead code testing...
        # self.check_reduce['while1elsestmt'] = 'tokens'
        return

    def reduce_is_invalid(self, rule, ast, tokens, first, last):
        if tokens is None:
            return False
        lhs = rule[0]

        # Dead code testing...
        # if lhs == 'while1elsestmt':
        #     from trepan.api import debug; debug()

        if lhs in ('aug_assign1', 'aug_assign2') and ast[0] and ast[0][0] == 'and':
            return True
        return False

class Python2ParserSingle(Python2Parser, PythonParserSingle):
    pass

if __name__ == '__main__':
    # Check grammar
    p = Python2Parser()
    p.check_grammar()
