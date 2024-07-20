#  Copyright (c) 2017-2024 Rocky Bernstein
"""
spark grammar differences over Python2 for Python 2.6.
"""

from spark_parser import DEFAULT_DEBUG as PARSER_DEFAULT_DEBUG

from uncompyle6.parser import PythonParserSingle
from uncompyle6.parsers.parse2 import Python2Parser
from uncompyle6.parsers.reducecheck import (
    except_handler,
    ifelsestmt2,
    ifstmt2,
    tryelsestmt,
    tryexcept,
)


class Python26Parser(Python2Parser):
    def __init__(self, debug_parser=PARSER_DEFAULT_DEBUG):
        super(Python26Parser, self).__init__(debug_parser)
        self.customized = {}

    def p_try_except26(self, args):
        """
        except_stmt    ::= except_cond3 except_suite
        except_cond1   ::= DUP_TOP expr COMPARE_OP
                           JUMP_IF_FALSE POP_TOP POP_TOP POP_TOP POP_TOP
        except_cond3   ::= DUP_TOP expr COMPARE_OP
                           JUMP_IF_FALSE POP_TOP POP_TOP store POP_TOP

        except_handler ::= JUMP_FORWARD COME_FROM except_stmts
                           come_froms_pop END_FINALLY come_froms

        except_handler ::= JUMP_FORWARD COME_FROM except_stmts
                           END_FINALLY

        except_handler ::= JUMP_FORWARD COME_FROM except_stmts
                           POP_TOP END_FINALLY
                           come_froms

        except_handler ::= jmp_abs COME_FROM except_stmts
                           POP_TOP END_FINALLY

        except_handler ::= jmp_abs COME_FROM except_stmts
                           END_FINALLY JUMP_FORWARD


        # Sometimes we don't put in COME_FROM to the next statement
        # like we do in 2.7. Perhaps we should?
        try_except     ::= SETUP_EXCEPT suite_stmts_opt POP_BLOCK
                            except_handler

        tryelsestmt    ::= SETUP_EXCEPT suite_stmts_opt POP_BLOCK
                           except_handler else_suite come_froms
        tryelsestmtl   ::= SETUP_EXCEPT suite_stmts_opt POP_BLOCK
                            except_handler else_suitel
        tryelsestmtc   ::= SETUP_EXCEPT suite_stmts_opt POP_BLOCK
                           except_handler else_suitec

        _ifstmts_jump  ::= c_stmts_opt JUMP_FORWARD COME_FROM POP_TOP

        except_suite   ::= c_stmts_opt JUMP_FORWARD come_from_pop
        except_suite   ::= c_stmts_opt jf_pop
        except_suite   ::= c_stmts_opt jmp_abs come_from_pop

        # This is what happens after a jump where
        # we start a new block. For reasons that I don't fully
        # understand, there is also a value on the top of the stack.
        come_from_pop   ::=  COME_FROM POP_TOP
        come_froms_pop  ::= come_froms POP_TOP
        """

    # In contrast to Python 2.7, Python 2.6 has a lot of
    # POP_TOP's which come right after various jumps.
    # The COME_FROM instructions our scanner adds, here it is to assist
    # distinguishing the extraneous POP_TOPs from those that start
    # after one of these jumps
    def p_jumps26(self, args):
        """

        # There are the equivalents of Python 2.7+'s
        # POP_JUMP_IF_TRUE and POP_JUMP_IF_FALSE
        jmp_true     ::= JUMP_IF_TRUE POP_TOP
        jmp_false    ::= JUMP_IF_FALSE POP_TOP

        jb_pop       ::= JUMP_BACK POP_TOP
        jf_pop       ::= JUMP_FORWARD POP_TOP

        jb_cont      ::= JUMP_BACK
        jb_cont      ::= CONTINUE

        jb_cf_pop ::= come_from_opt JUMP_BACK _come_froms POP_TOP
        ja_cf_pop ::= JUMP_ABSOLUTE come_froms POP_TOP
        jf_cf_pop ::= JUMP_FORWARD come_froms POP_TOP

        # The first optional COME_FROM when it appears is really
        # COME_FROM_LOOP, but in <= 2.6 we don't distinguish
        # this

        cf_jb_cf_pop ::= _come_froms JUMP_BACK come_froms POP_TOP

        pb_come_from    ::= POP_BLOCK COME_FROM
        jb_pb_come_from ::= JUMP_BACK pb_come_from

        _ifstmts_jump ::= c_stmts_opt JUMP_FORWARD COME_FROM POP_TOP
        _ifstmts_jump ::= c_stmts_opt JUMP_FORWARD come_froms POP_TOP COME_FROM

        # This is what happens after a jump where
        # we start a new block. For reasons that I don't fully
        # understand, there is also a value on the top of the stack.
        come_froms_pop  ::=  come_froms POP_TOP

        """

    def p_stmt26(self, args):
        """
        stmt ::= ifelsestmtr

        # We use filler as a placeholder to keep nonterminal positions
        # the same across different grammars so that the same semantic actions
        # can be used
        filler ::=

        assert ::= assert_expr jmp_true LOAD_ASSERT RAISE_VARARGS_1 come_froms_pop
        assert2 ::= assert_expr jmp_true LOAD_ASSERT expr RAISE_VARARGS_2 come_froms_pop

        break ::= BREAK_LOOP JUMP_BACK

        # Semantic actions want else_suitel to be at index 3
        ifelsestmtl ::= testexpr c_stmts_opt cf_jb_cf_pop else_suitel
        ifelsestmtc ::= testexpr c_stmts_opt ja_cf_pop    else_suitec
        ifelsestmt ::=  testexpr stmts_opt ja_cf_pop      else_suite

        stmts_opt ::= stmts
        stmts_opt ::=

        # The last except of a "try: ... except" can do this...
        except_suite ::= stmts_opt COME_FROM JUMP_ABSOLUTE POP_TOP

        # Semantic actions want suite_stmts_opt to be at index 3
        with        ::= expr setupwith SETUP_FINALLY suite_stmts_opt
                        POP_BLOCK LOAD_CONST COME_FROM WITH_CLEANUP END_FINALLY

        # Semantic actions want store to be at index 2
        with_as ::= expr setupwithas store suite_stmts_opt
                       POP_BLOCK LOAD_CONST COME_FROM WITH_CLEANUP END_FINALLY

        # This is truly weird. 2.7 does this (not including POP_TOP) with
        # opcode SETUP_WITH

        setupwith     ::= DUP_TOP LOAD_ATTR ROT_TWO LOAD_ATTR CALL_FUNCTION_0 POP_TOP
        setupwithas   ::= DUP_TOP LOAD_ATTR ROT_TWO LOAD_ATTR CALL_FUNCTION_0 setup_finally

        setup_finally ::= STORE_FAST SETUP_FINALLY LOAD_FAST DELETE_FAST
        setup_finally ::= STORE_NAME SETUP_FINALLY LOAD_NAME DELETE_NAME

        while1stmt     ::= SETUP_LOOP l_stmts_opt come_from_opt JUMP_BACK _come_froms

        # Sometimes JUMP_BACK is misclassified as CONTINUE.
        # workaround until we have better control flow in place
        while1stmt     ::= SETUP_LOOP l_stmts_opt CONTINUE _come_froms

        whilestmt      ::= SETUP_LOOP testexpr l_stmts_opt jb_pop POP_BLOCK _come_froms
        whilestmt      ::= SETUP_LOOP testexpr l_stmts_opt jb_cf_pop pb_come_from
        whilestmt      ::= SETUP_LOOP testexpr l_stmts_opt jb_cf_pop POP_BLOCK
        whilestmt      ::= SETUP_LOOP testexpr returns POP_BLOCK COME_FROM

        # In the "whilestmt" below, there isn't a COME_FROM when the
        # "while" is the last thing in the module or function.

        whilestmt      ::= SETUP_LOOP testexpr returns POP_TOP POP_BLOCK

        whileelsestmt  ::= SETUP_LOOP testexpr l_stmts_opt jb_pop POP_BLOCK
                           else_suitel COME_FROM
        while1elsestmt ::= SETUP_LOOP l_stmts JUMP_BACK else_suitel COME_FROM

        return         ::= return_expr RETURN_END_IF POP_TOP
        return         ::= return_expr RETURN_VALUE POP_TOP
        return_if_stmt ::= return_expr RETURN_END_IF POP_TOP

        iflaststmtl ::= testexpr c_stmts_opt jb_cf_pop
        iflaststmt  ::= testexpr c_stmts_opt JUMP_ABSOLUTE come_from_pop

        lastc_stmt ::= iflaststmt come_froms

        ifstmt         ::= testexpr_then _ifstmts_jump

        # Semantic actions want the else to be at position 3
        ifelsestmt     ::= testexpr_then c_stmts_opt jf_cf_pop else_suite come_froms
        ifelsestmt     ::= testexpr_then c_stmts_opt filler else_suitel come_froms POP_TOP
        ifelsestmt     ::= testexpr c_stmts_opt jf_cf_pop else_suite

        # We have no jumps to jumps, so no "come_froms" but a single "COME_FROM"
        ifelsestmt     ::= testexpr      c_stmts_opt jf_cf_pop else_suite COME_FROM

        # Semantic actions want else_suitel to be at index 3
        ifelsestmtl    ::= testexpr_then c_stmts_opt jb_cf_pop else_suitel
        ifelsestmtc    ::= testexpr_then c_stmts_opt ja_cf_pop else_suitec

        iflaststmt     ::= testexpr_then c_stmts_opt JUMP_ABSOLUTE come_froms POP_TOP
        iflaststmt     ::= testexpr      c_stmts_opt JUMP_ABSOLUTE come_froms POP_TOP

        # "if"/"else" statement that ends in a RETURN
        ifelsestmtr    ::= testexpr_then return_if_stmts returns

        testexpr_then  ::= testtrue_then
        testexpr_then  ::= testfalse_then
        testtrue_then  ::= expr jmp_true_then
        testfalse_then ::= expr jmp_false_then

        jmp_false_then ::= JUMP_IF_FALSE THEN POP_TOP
        jmp_true_then  ::= JUMP_IF_TRUE THEN POP_TOP

        # In the "while1stmt" below, there sometimes isn't a
        # "COME_FROM" when the "while1" is the last thing in the
        # module or function.

        while1stmt ::= SETUP_LOOP returns come_from_opt
        for_block  ::= returns _come_froms
        """

    def p_comp26(self, args):
        """
        list_for ::= expr for_iter store list_iter JUMP_BACK come_froms POP_TOP

        # The JUMP FORWARD below jumps to the JUMP BACK. It seems to happen
        # in rare cases that may have to with length of code
        # FIXME: we can add a reduction check for this

        list_for ::= expr for_iter store list_iter JUMP_FORWARD come_froms POP_TOP
                     COME_FROM JUMP_BACK

        list_for ::= expr for_iter store list_iter jb_cont

        # This is for a really funky:
        #   [  x for x in range(10) if x % 2 if x % 3 ]
        # the JUMP_ABSOLUTE is to the instruction after the last POP_TOP
        #  we have a reduction check for this

        list_for ::= expr for_iter store list_iter JUMP_ABSOLUTE come_froms
                     POP_TOP jb_pop

        list_iter  ::= list_if JUMP_BACK
        list_iter  ::= list_if JUMP_BACK COME_FROM POP_TOP
        list_comp  ::= BUILD_LIST_0 DUP_TOP
                       store list_iter delete
        list_comp  ::= BUILD_LIST_0 DUP_TOP
                       store list_iter JUMP_BACK delete
        lc_body    ::= LOAD_NAME expr LIST_APPEND
        lc_body    ::= LOAD_FAST expr LIST_APPEND

        comp_for ::= SETUP_LOOP expr for_iter store comp_iter jb_pb_come_from

        comp_iter   ::= comp_if_not
        comp_if_not ::= expr jmp_true comp_iter

        comp_body   ::= gen_comp_body

        for_block ::= l_stmts_opt _come_froms POP_TOP JUMP_BACK

        # Make sure we keep indices the same as 2.7

        setup_loop_lf ::= SETUP_LOOP LOAD_FAST
        genexpr_func ::= setup_loop_lf FOR_ITER store comp_iter jb_pb_come_from
        genexpr_func ::= setup_loop_lf FOR_ITER store comp_iter JUMP_BACK come_from_pop
                         jb_pb_come_from

        # This is for a really funky:
        #   (x for x in range(10) if x % 2 if x % 3 )
        # the JUMP_ABSOLUTE is to the instruction after the last POP_TOP.
        # Add a reduction check for this?

        genexpr_func ::= setup_loop_lf FOR_ITER store comp_iter JUMP_ABSOLUTE come_froms
                         POP_TOP jb_pop jb_pb_come_from

        genexpr_func ::= setup_loop_lf FOR_ITER store comp_iter JUMP_BACK come_froms
                         POP_TOP jb_pb_come_from

        generator_exp ::= LOAD_GENEXPR MAKE_FUNCTION_0 expr GET_ITER CALL_FUNCTION_1 COME_FROM
        list_if ::= expr jmp_false_then list_iter
        """

    def p_ret26(self, args):
        """
        ret_and      ::= expr jmp_false return_expr_or_cond COME_FROM
        ret_or       ::= expr jmp_true return_expr_or_cond COME_FROM
        if_exp_ret   ::= expr jmp_false_then expr RETURN_END_IF POP_TOP return_expr_or_cond
        if_exp_ret   ::= expr jmp_false_then expr return_expr_or_cond

        return_if_stmt ::= return_expr RETURN_END_IF POP_TOP
        return ::= return_expr RETURN_VALUE POP_TOP

        # FIXME: split into Python 2.5
        ret_or   ::= expr jmp_true return_expr_or_cond come_froms
        """

    def p_except26(self, args):
        """
        except_suite ::= c_stmts_opt jmp_abs POP_TOP
        """

    def p_misc26(self, args):
        """
        dict ::= BUILD_MAP kvlist
        kvlist ::= kvlist kv3

        # Note: preserve positions 0 2 and 4 for semantic actions
        if_exp_not         ::= expr jmp_true  expr jf_cf_pop expr COME_FROM
        if_exp             ::= expr jmp_false expr jf_cf_pop expr come_from_opt
        if_exp             ::= expr jmp_false expr ja_cf_pop expr

        expr               ::= if_exp_not

        and                ::= expr JUMP_IF_FALSE POP_TOP expr JUMP_IF_FALSE POP_TOP

        # A "compare_chained" is two comparisons like x <= y <= z
        compare_chained          ::= expr compared_chained_middle ROT_TWO
                                     COME_FROM POP_TOP _come_froms
        compared_chained_middle  ::= expr DUP_TOP ROT_THREE COMPARE_OP
                                     jmp_false compared_chained_middle _come_froms
        compared_chained_middle   ::= expr DUP_TOP ROT_THREE COMPARE_OP
                                     jmp_false compare_chained_right _come_froms

        compared_chained_middle   ::= expr DUP_TOP ROT_THREE COMPARE_OP
                                      jmp_false_then compared_chained_middle _come_froms
        compared_chained_middle   ::= expr DUP_TOP ROT_THREE COMPARE_OP
                                      jmp_false_then compare_chained_right _come_froms

        compare_chained_right   ::= expr COMPARE_OP return_expr_lambda
        compare_chained_right   ::= expr COMPARE_OP RETURN_END_IF_LAMBDA
        compare_chained_right   ::= expr COMPARE_OP RETURN_END_IF COME_FROM

        return_if_lambda   ::= RETURN_END_IF_LAMBDA POP_TOP
        stmt               ::= if_exp_lambda
        stmt               ::= if_exp_not_lambda
        if_exp_lambda      ::= expr jmp_false_then expr return_if_lambda
                               return_stmt_lambda LAMBDA_MARKER
        if_exp_not_lambda ::=
                               expr jmp_true_then expr return_if_lambda
                               return_stmt_lambda LAMBDA_MARKER

        # if_exp_true are for conditions which always evaluate true
        # There is dead or non-optional remnants of the condition code though,
        # and we use that to match on to reconstruct the source more accurately
        expr               ::= if_exp_true
        if_exp_true        ::= expr jf_pop expr COME_FROM

        # This comes from
        #   0 or max(5, 3) if 0 else 3
        # where there seems to be an additional COME_FROM at the
        # end. Not sure if this is appropriately named or
        # is the best way to handle
        expr               ::= if_exp_false
        if_exp_false  ::= if_exp COME_FROM

        """

    def customize_grammar_rules(self, tokens, customize):
        self.remove_rules(
            """
        with_as ::= expr SETUP_WITH store suite_stmts_opt
                    POP_BLOCK LOAD_CONST COME_FROM_WITH
                    WITH_CLEANUP END_FINALLY
        """
        )
        super(Python26Parser, self).customize_grammar_rules(tokens, customize)
        self.reduce_check_table = {
            "except_handler": except_handler,
            "ifstmt": ifstmt2,
            "ifelsestmt": ifelsestmt2,
            "tryelsestmt": tryelsestmt,
            "try_except": tryexcept,
            "tryelsestmtl": tryelsestmt,
        }

        self.check_reduce["and"] = "AST"
        self.check_reduce["assert_expr_and"] = "AST"
        self.check_reduce["except_handler"] = "tokens"
        self.check_reduce["ifstmt"] = "AST"
        self.check_reduce["ifelsestmt"] = "AST"
        self.check_reduce["forelselaststmtl"] = "tokens"
        self.check_reduce["forelsestmt"] = "tokens"
        self.check_reduce["list_for"] = "AST"
        self.check_reduce["try_except"] = "AST"
        self.check_reduce["tryelsestmt"] = "AST"
        self.check_reduce["tryelsestmtl"] = "AST"

    def reduce_is_invalid(self, rule, ast, tokens, first, last):
        invalid = super(Python26Parser, self).reduce_is_invalid(
            rule, ast, tokens, first, last
        )
        lhs = rule[0]
        if invalid or tokens is None:
            return invalid
        if rule in (
            ("and", ("expr", "jmp_false", "expr", "\\e_come_from_opt")),
            ("and", ("expr", "jmp_false", "expr", "come_from_opt")),
            ("assert_expr_and", ("assert_expr", "jmp_false", "expr")),
        ):
            # FIXME: workaround profiling bug
            if ast[1] is None:
                return False

            # For now, we won't let the 2nd 'expr' be an "if_exp_not"
            # However in < 2.6 where we don't have if/else expression it *can*
            # be.
            if self.version >= (2, 6) and ast[2][0] == "if_exp_not":
                return True

            test_index = last
            while tokens[test_index].kind == "COME_FROM":
                test_index += 1
            if tokens[test_index].kind.startswith("JUMP_IF"):
                return False

            # Test that jmp_false jumps to the end of "and"
            # or that it jumps to the same place as the end of "and"
            jmp_false = ast[1][0]
            jmp_target = jmp_false.offset + jmp_false.attr + 3

            return not (
                jmp_target == tokens[test_index].offset
                or tokens[last].pattr == jmp_false.pattr
            )

        elif lhs in ("forelselaststmtl", "forelsestmt"):
            # print("XXX", first, last)
            # for t in range(first, last):
            #     print(tokens[t])
            # print("=" * 30)

            # If the SETUP_LOOP jumps to the tokens[last] then
            # this is a "for" not a "for else".

            # However, in Python 2.2 and before there is a SET_LINENO
            # instruction which might have gotten removed. So we need
            # to account for that.  bytecode-1.4/anydbm.pyc exhibits
            # this behavior.

            # Also we need to use the setup_loop instruction (not opcode)
            # since the operand can be a relative offset rather than
            # an absolute offset.
            setup_inst = self.insts[self.offset2inst_index[tokens[first].offset]]
            last = min(len(tokens) - 1, last)
            if self.version <= (2, 2) and tokens[last] == "COME_FROM":
                last += 1
            return tokens[last - 1].off2int() > setup_inst.argval
        elif rule == ("ifstmt", ("testexpr", "_ifstmts_jump")):
            for i in range(last - 1, last - 4, -1):
                t = tokens[i]
                if t == "JUMP_FORWARD":
                    return t.attr > tokens[min(last, len(tokens) - 1)].off2int()
                elif t not in ("POP_TOP", "COME_FROM"):
                    break
                pass
            pass
        elif rule == (
            "list_for",
            (
                "expr",
                "for_iter",
                "store",
                "list_iter",
                "JUMP_ABSOLUTE",
                "come_froms",
                "POP_TOP",
                "jb_pop",
            ),
        ):
            # The JUMP_ABSOLUTE has to be to the last POP_TOP or this is invalid
            ja_attr = ast[4].attr
            return tokens[last].offset != ja_attr
        elif lhs == "try_except":
            # We need to distinguish "try_except" from "tryelsestmt"; we do that
            # by looking for a jump before the END_FINALLY to the "else" clause of
            # "try else".
            #
            # If we have:
            #    <insn>
            #    POP_TOP
            #    END_FINALLY
            #    COME_FROM
            # then <insn> has to be either a a jump of some sort (JUMP_FORWARD, BREAK_LOOP, JUMP_BACK, or RETURN_VALUE).
            # Furthermore, if it is JUMP_FORWARD, then it has to be a JUMP_FORWARD to right after
            # COME_FROM
            if last == len(tokens):
                last -= 1
            if tokens[last] != "COME_FROM" and tokens[last - 1] == "COME_FROM":
                last -= 1
            if (
                tokens[last] == "COME_FROM"
                and tokens[last - 1] == "END_FINALLY"
                and tokens[last - 2] == "POP_TOP"
            ):
                # A jump of 2 is a jump around POP_TOP, END_FINALLY which
                # would indicate try/else rather than try
                return tokens[last - 3].kind not in frozenset(
                    ("JUMP_FORWARD", "JUMP_BACK", "BREAK_LOOP", "RETURN_VALUE")
                ) or (tokens[last - 3] == "JUMP_FORWARD" and tokens[last - 3].attr != 2)

        return False


class Python26ParserSingle(Python2Parser, PythonParserSingle):
    pass


if __name__ == "__main__":
    # Check grammar
    p = Python26Parser()
    p.check_grammar()
    from xdis.version_info import IS_PYPY, PYTHON_VERSION_TRIPLE

    if PYTHON_VERSION_TRIPLE[:2] == (2, 6):
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
        # print(sorted(p.rule2name.items()))
