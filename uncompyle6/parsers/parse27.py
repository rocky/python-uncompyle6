#  Copyright (c) 2016-2020, 2022 Rocky Bernstein
#  Copyright (c) 2005 by Dan Pascu <dan@windowmaker.org>
#  Copyright (c) 2000-2002 by hartmut Goebel <hartmut@goebel.noris.de>

from spark_parser import DEFAULT_DEBUG as PARSER_DEFAULT_DEBUG
from xdis import next_offset

from uncompyle6.parser import PythonParserSingle, nop_func
from uncompyle6.parsers.parse2 import Python2Parser
from uncompyle6.parsers.reducecheck import (
    aug_assign1_check,
    except_handler,
    for_block_check,
    ifelsestmt,
    or_check,
    tryelsestmt,
)


class Python27Parser(Python2Parser):
    def __init__(self, debug_parser=PARSER_DEFAULT_DEBUG):
        super(Python27Parser, self).__init__(debug_parser)
        self.customized = {}

    def p_comprehension27(self, args):
        """
        list_for  ::= expr for_iter store list_iter JUMP_BACK
        list_comp ::= BUILD_LIST_0 list_iter
        lc_body   ::= expr LIST_APPEND
        for_iter  ::= GET_ITER COME_FROM FOR_ITER

        stmt ::= set_comp_func


        # Dictionary and set comprehensions were added in Python 2.7
        expr      ::= dict_comp
        dict_comp ::= LOAD_DICTCOMP MAKE_FUNCTION_0 expr GET_ITER CALL_FUNCTION_1

        stmt           ::= dict_comp_func
        dict_comp_func ::= BUILD_MAP_0 LOAD_FAST FOR_ITER store
                           comp_iter JUMP_BACK RETURN_VALUE RETURN_LAST

        set_comp_func ::= BUILD_SET_0 LOAD_FAST FOR_ITER store comp_iter
                          JUMP_BACK RETURN_VALUE RETURN_LAST

        comp_iter     ::= comp_if_not
        comp_if_not   ::= expr jmp_true comp_iter

        comp_body ::= dict_comp_body
        comp_body ::= set_comp_body
        comp_for ::= expr for_iter store comp_iter JUMP_BACK

        dict_comp_body ::= expr expr MAP_ADD
        set_comp_body ::= expr SET_ADD

        # See also common Python p_list_comprehension
        """

    def p_try27(self, args):
        """
        # If the last except is a "raise" we might not have a final COME_FROM
        # FIXME: need a check on this rule since this accepts try_except when
        # we shouldn't
        try_except      ::= SETUP_EXCEPT suite_stmts_opt POP_BLOCK
                            except_handler

        tryfinallystmt ::= SETUP_FINALLY suite_stmts_opt
                           POP_BLOCK LOAD_CONST
                           COME_FROM_FINALLY suite_stmts_opt END_FINALLY

        tryelsestmt    ::= SETUP_EXCEPT suite_stmts_opt POP_BLOCK
                           except_handler_else else_suite COME_FROM

        tryelsestmtl   ::= SETUP_EXCEPT suite_stmts_opt POP_BLOCK
                           except_handler_else else_suitel JUMP_BACK COME_FROM

        tryelsestmtl   ::= SETUP_EXCEPT suite_stmts_opt POP_BLOCK
                           except_handler_else else_suitel
        tryelsestmtc   ::= SETUP_EXCEPT suite_stmts_opt POP_BLOCK
                           except_handler_else else_suitec COME_FROM

        except_stmt ::= except_cond2 except_suite

        except_cond1 ::= DUP_TOP expr COMPARE_OP
                         jmp_false POP_TOP POP_TOP POP_TOP

        except_cond2 ::= DUP_TOP expr COMPARE_OP
                         jmp_false POP_TOP store POP_TOP

        for_block    ::= l_stmts_opt JUMP_BACK

        # In 2.7 there is occasionally a for_block has an unusual
        # form: there is a JUMP_ABSOLUTE which jumps to the second JUMP_BACK
        # listed below. Both JUMP_BACKS go to the same position so the
        # the JUMP_ABSOLUTE and JUMP_BACK not necessary
        for_block    ::= l_stmts_opt JUMP_ABSOLUTE JUMP_BACK JUMP_BACK
        """

    def p_jump27(self, args):
        """
        iflaststmtl     ::= testexpr c_stmts

        _ifstmts_jump   ::= c_stmts_opt JUMP_FORWARD come_froms
        pb_come_from    ::= POP_BLOCK COME_FROM

        # FIXME: Common with 3.0+
        jmp_false ::= POP_JUMP_IF_FALSE
        jmp_true  ::= POP_JUMP_IF_TRUE

        ret_and    ::= expr JUMP_IF_FALSE_OR_POP return_expr_or_cond COME_FROM
        ret_or     ::= expr JUMP_IF_TRUE_OR_POP return_expr_or_cond COME_FROM
        if_exp_ret ::= expr POP_JUMP_IF_FALSE expr RETURN_END_IF COME_FROM return_expr_or_cond

        expr_jitop ::= expr JUMP_IF_TRUE_OR_POP
        or         ::= expr_jitop expr COME_FROM
        and        ::= expr JUMP_IF_FALSE_OR_POP expr COME_FROM

        # compare_chained{1,2} is used exclusively in chained_compare
        compare_chained1 ::= expr DUP_TOP ROT_THREE COMPARE_OP JUMP_IF_FALSE_OR_POP
                             compare_chained1 COME_FROM
        compare_chained1 ::= expr DUP_TOP ROT_THREE COMPARE_OP JUMP_IF_FALSE_OR_POP
                             compare_chained2 COME_FROM

        return_lambda      ::= RETURN_VALUE
        return_lambda      ::= RETURN_VALUE_LAMBDA

        compare_chained2 ::= expr COMPARE_OP return_lambda
        compare_chained2 ::= expr COMPARE_OP return_lambda

        # if_exp_true are for conditions which always evaluate true
        # There is dead or non-optional remnants of the condition code though,
        # and we use that to match on to reconstruct the source more accurately.
        # FIXME: we should do analysis and reduce *only* if there is dead code?
        #        right now we check that expr is "or". Any other nodes types?

        expr             ::= if_exp_true
        if_exp_true      ::= expr JUMP_FORWARD expr COME_FROM

        if_exp           ::= expr jmp_false expr JUMP_FORWARD expr COME_FROM
        if_exp           ::= expr jmp_false expr JUMP_ABSOLUTE expr
        """

    def p_stmt27(self, args):
        """
        stmt ::= ifelsestmtr
        stmt ::= ifelsestmtc

        # assert condition
        assert        ::= assert_expr jmp_true LOAD_ASSERT RAISE_VARARGS_1

        # assert condition, expr
        assert2    ::= assert_expr jmp_true LOAD_ASSERT expr CALL_FUNCTION_1 RAISE_VARARGS_1

        continue   ::= JUMP_BACK JUMP_ABSOLUTE

        for_block  ::= returns _come_froms

        with       ::= expr SETUP_WITH POP_TOP suite_stmts_opt
                       POP_BLOCK LOAD_CONST COME_FROM_WITH
                       WITH_CLEANUP END_FINALLY

        withasstmt ::= expr SETUP_WITH store suite_stmts_opt
                POP_BLOCK LOAD_CONST COME_FROM_WITH
                WITH_CLEANUP END_FINALLY

        whilestmt         ::= SETUP_LOOP testexpr returns
                              _come_froms POP_BLOCK COME_FROM


        # 2.7.5 (and before to 2.7.0?)
        while1stmt        ::= SETUP_LOOP l_stmts_opt JUMP_BACK COME_FROM
        while1stmt        ::= SETUP_LOOP l_stmts_opt CONTINUE COME_FROM
        while1stmt        ::= SETUP_LOOP returns COME_FROM
        while1elsestmt    ::= SETUP_LOOP l_stmts JUMP_BACK
                              else_suitel COME_FROM

        while1stmt        ::= SETUP_LOOP returns pb_come_from
        while1stmt        ::= SETUP_LOOP l_stmts_opt JUMP_BACK POP_BLOCK COME_FROM

        whilestmt         ::= SETUP_LOOP testexpr l_stmts_opt JUMP_BACK POP_BLOCK _come_froms

        # Should this be JUMP_BACK+ ?
        # JUMP_BACK should all be to the same location
        whilestmt         ::= SETUP_LOOP testexpr l_stmts_opt JUMP_BACK JUMP_BACK POP_BLOCK _come_froms

        while1elsestmt    ::= SETUP_LOOP l_stmts JUMP_BACK POP_BLOCK
                              else_suitel COME_FROM
        whileelsestmt     ::= SETUP_LOOP testexpr l_stmts_opt JUMP_BACK POP_BLOCK
                              else_suitel COME_FROM

        return_stmts      ::= _stmts return_stmt
        return_stmts      ::= return_stmt
        return_stmt       ::= return

        ifstmt            ::= testexpr return_stmts COME_FROM
        ifstmt            ::= testexpr return_if_stmts COME_FROM
        ifelsestmt        ::= testexpr c_stmts_opt JUMP_FORWARD else_suite come_froms
        ifelsestmtc       ::= testexpr c_stmts_opt JUMP_ABSOLUTE else_suitec
        ifelsestmtc       ::= testexpr c_stmts_opt JUMP_FORWARD else_suite come_froms
        ifelsestmtl       ::= testexpr c_stmts_opt JUMP_BACK else_suitel
        ifelsestmtl       ::= testexpr c_stmts_opt CONTINUE else_suitel

        # In the future when we have ifelsestmtl checking we should add something like:
        # ifelsestmtl       ::= testexpr c_stmts_opt JUMP_FORWARD else_suite come_froms
        # c_stmts           ::= ifelsestmtl

        # "if"/"else" statement that ends in a RETURN
        ifelsestmtr       ::= testexpr return_if_stmts COME_FROM returns

        # Common with 2.6
        return_if_lambda   ::= RETURN_END_IF_LAMBDA COME_FROM
        stmt               ::= if_exp_lambda
        stmt               ::= if_exp_not_lambda
        if_exp_lambda      ::= expr jmp_false expr return_if_lambda
                               return_stmt_lambda LAMBDA_MARKER
        if_exp_not_lambda  ::= expr jmp_true expr return_if_lambda
                               return_stmt_lambda LAMBDA_MARKER

        expr               ::= if_exp_not
        if_exp_not         ::= expr jmp_true expr _jump expr COME_FROM

        kv3 ::= expr expr STORE_MAP
        """

    def customize_grammar_rules(self, tokens, customize):
        # 2.7 changes COME_FROM to COME_FROM_FINALLY
        self.remove_rules(
            """
        while1elsestmt ::= SETUP_LOOP l_stmts JUMP_BACK else_suite COME_FROM
        tryfinallystmt ::= SETUP_FINALLY suite_stmts_opt
                           POP_BLOCK LOAD_CONST COME_FROM suite_stmts_opt
                           END_FINALLY
        """
        )
        if "PyPy" in customize:
            # PyPy-specific customizations
            self.addRule(
                """
                        return_if_stmt ::= return_expr RETURN_END_IF come_froms
                        """,
                nop_func,
            )

        super(Python27Parser, self).customize_grammar_rules(tokens, customize)

        # FIXME: Put more in this table
        self.reduce_check_table = {
            "aug_assign1": aug_assign1_check,
            "except_handler": except_handler,
            "for_block": for_block_check.for_block_invalid,
            "ifelsestmt": ifelsestmt,
            "ifelsestmtc": ifelsestmt,
            "or": or_check,
            "tryelsestmt": tryelsestmt,
            "tryelsestmtl": tryelsestmt,
        }

        self.check_reduce["and"] = "AST"
        self.check_reduce["aug_assign1"] = "AST"
        self.check_reduce["if_exp"] = "AST"

        self.check_reduce["except_handler"] = "tokens"
        self.check_reduce["except_handler_else"] = "tokens"

        self.check_reduce["for_block"] = "tokens"

        self.check_reduce["or"] = "AST"
        self.check_reduce["raise_stmt1"] = "AST"
        self.check_reduce["ifelsestmt"] = "AST"
        self.check_reduce["ifelsestmtc"] = "AST"
        self.check_reduce["iflaststmtl"] = "AST"
        self.check_reduce["list_if_not"] = "AST"
        self.check_reduce["list_if"] = "AST"
        self.check_reduce["comp_if"] = "AST"
        self.check_reduce["if_exp_true"] = "tokens"
        self.check_reduce["whilestmt"] = "tokens"

        return

    def reduce_is_invalid(self, rule, ast, tokens, first, last):
        invalid = super(Python27Parser, self).reduce_is_invalid(
            rule, ast, tokens, first, last
        )

        lhs = rule[0]
        n = len(tokens)
        fn = self.reduce_check_table.get(lhs, None)
        if fn:
            invalid = fn(self, lhs, n, rule, ast, tokens, first, last)
        last = min(last, n - 1)
        if invalid:
            return invalid

        if rule == ("comp_if", ("expr", "jmp_false", "comp_iter")):
            jmp_false = ast[1]
            if jmp_false[0] == "POP_JUMP_IF_FALSE":
                return tokens[first].offset < jmp_false[0].attr < tokens[last].offset
            pass
        elif (rule[0], rule[1][0:5]) == (
            "if_exp",
            ("expr", "jmp_false", "expr", "JUMP_ABSOLUTE", "expr"),
        ):
            jmp_false = ast[1]
            if jmp_false[0] == "POP_JUMP_IF_FALSE":
                else_instr = ast[4].first_child()
                if jmp_false[0].attr != else_instr.offset:
                    return True
                end_offset = ast[3].attr
                return end_offset < tokens[last].offset
            pass
        elif rule[0] == "raise_stmt1":
            return ast[0] == "expr" and ast[0][0] == "or"
        elif rule[0] in ("assert", "assert2"):
            jump_inst = ast[1][0]
            jump_target = jump_inst.attr
            return not (
                last >= len(tokens)
                or jump_target == tokens[last].offset
                or jump_target == next_offset(ast[-1].op, ast[-1].opc, ast[-1].offset)
            )
        elif rule == ("ifstmt", ("testexpr", "_ifstmts_jump")):
            for i in range(last - 1, last - 4, -1):
                t = tokens[i]
                if t == "JUMP_FORWARD":
                    return t.attr > tokens[min(last, len(tokens) - 1)].off2int()
                elif t not in ("POP_TOP", "COME_FROM"):
                    break
                pass
            pass
        elif rule == ("iflaststmtl", ("testexpr", "c_stmts")):
            testexpr = ast[0]
            if testexpr[0] in ("testfalse", "testtrue"):
                test = testexpr[0]
                if len(test) > 1 and test[1].kind.startswith("jmp_"):
                    jmp_target = test[1][0].attr
                    if last == len(tokens):
                        last -= 1
                    while isinstance(tokens[first].offset, str) and first < last:
                        first += 1
                    if first == last:
                        return True
                    while first < last and isinstance(tokens[last].offset, str):
                        last -= 1
                    return tokens[first].off2int() < jmp_target < tokens[last].off2int()
                    pass
                pass
            pass
        elif rule == ("list_if_not", ("expr", "jmp_true", "list_iter")):
            jump_inst = ast[1][0]
            jump_offset = jump_inst.attr
            return jump_inst.offset < jump_offset < tokens[last].offset
        elif rule == ("list_if", ("expr", "jmp_false", "list_iter")):
            jump_inst = ast[1][0]
            jump_offset = jump_inst.attr
            return jump_inst.offset < jump_offset < tokens[last].offset
        elif rule == ("or", ("expr", "jmp_true", "expr", "\\e_come_from_opt")):
            # Test that jmp_true doesn't jump inside the middle the "or"
            # or that it jumps to the same place as the end of "and"
            jmp_true = ast[1][0]
            jmp_target = jmp_true.offset + jmp_true.attr + 3
            return not (
                jmp_target == tokens[last].offset
                or tokens[last].pattr == jmp_true.pattr
            )

        elif rule[0] == "whilestmt" and rule[1][0:-2] == (
            "SETUP_LOOP",
            "testexpr",
            "l_stmts_opt",
            "JUMP_BACK",
            "JUMP_BACK",
        ):
            # Make sure that the jump backs all go to the same place
            i = last - 1
            while tokens[i] != "JUMP_BACK":
                i -= 1
            return tokens[i].attr != tokens[i - 1].attr
        elif rule[0] == "if_exp_true":
            return (first) > 0 and tokens[first - 1] == "POP_JUMP_IF_FALSE"

        return False


class Python27ParserSingle(Python27Parser, PythonParserSingle):
    pass


if __name__ == "__main__":
    # Check grammar
    p = Python27Parser()
    p.check_grammar()
    from xdis.version_info import IS_PYPY, PYTHON_VERSION_TRIPLE

    if PYTHON_VERSION_TRIPLE[:2] == (2, 7):
        lhs, rhs, tokens, right_recursive, dup_rhs = p.check_sets()
        from uncompyle6.scanner import get_scanner

        s = get_scanner(PYTHON_VERSION_TRIPLE, IS_PYPY)
        opcode_set = set(s.opc.opname).union(
            set(
                """JUMP_BACK CONTINUE RETURN_END_IF COME_FROM
               LOAD_GENEXPR LOAD_ASSERT LOAD_SETCOMP LOAD_DICTCOMP
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
        p.check_grammar()
        p.dump_grammar()
