#  Copyright (c) 2017-2020, 2022 Rocky Bernstein
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
spark grammar differences over Python 3.7 for Python 3.8
"""
from __future__ import print_function

from uncompyle6.parser import PythonParserSingle, nop_func
from spark_parser import DEFAULT_DEBUG as PARSER_DEFAULT_DEBUG
from uncompyle6.parsers.parse37 import Python37Parser

class Python38Parser(Python37Parser):
    def p_38_stmt(self, args):
        """
        stmt               ::= async_for_stmt38
        stmt               ::= async_forelse_stmt38
        stmt               ::= call_stmt
        stmt               ::= continue
        stmt               ::= for38
        stmt               ::= forelselaststmt38
        stmt               ::= forelselaststmtl38
        stmt               ::= forelsestmt38
        stmt               ::= try_elsestmtl38
        stmt               ::= try_except38
        stmt               ::= try_except38r
        stmt               ::= try_except38r2
        stmt               ::= try_except38r3
        stmt               ::= try_except38r4
        stmt               ::= try_except_as
        stmt               ::= try_except_ret38
        stmt               ::= tryfinally38astmt
        stmt               ::= tryfinally38rstmt
        stmt               ::= tryfinally38rstmt2
        stmt               ::= tryfinally38rstmt3
        stmt               ::= tryfinally38stmt
        stmt               ::= whileTruestmt38
        stmt               ::= whilestmt38

        call_stmt          ::= call
        break ::= POP_BLOCK BREAK_LOOP
        break ::= POP_BLOCK POP_TOP BREAK_LOOP
        break ::= POP_TOP BREAK_LOOP
        break ::= POP_EXCEPT BREAK_LOOP

        # The "continue" rule is a weird one. In 3.8, CONTINUE_LOOP was removed.
        # Inside an loop we can have this, which can only appear in side a try/except
        # And it can also appear at the end of the try except.
        continue           ::= POP_EXCEPT JUMP_BACK


        # FIXME: this should be restricted to being inside a try block
        stmt               ::= except_ret38
        stmt               ::= except_ret38a

        # FIXME: this should be added only when seeing GET_AITER or YIELD_FROM
        async_for          ::= GET_AITER _come_froms
                               SETUP_FINALLY GET_ANEXT LOAD_CONST YIELD_FROM POP_BLOCK
        async_for_stmt38   ::= expr async_for
                               store for_block
                               COME_FROM_FINALLY
                               END_ASYNC_FOR

       genexpr_func_async  ::= LOAD_ARG func_async_prefix
                               store comp_iter
                               JUMP_BACK COME_FROM_FINALLY
                               END_ASYNC_FOR

        # FIXME: come froms after the else_suite or END_ASYNC_FOR distinguish which of
        # for / forelse is used. Add come froms and check of add up control-flow detection phase.
        async_forelse_stmt38 ::= expr
                               GET_AITER
                               SETUP_FINALLY
                               GET_ANEXT
                               LOAD_CONST
                               YIELD_FROM
                               POP_BLOCK
                               store for_block
                               COME_FROM_FINALLY
                               END_ASYNC_FOR
                               else_suite

        # Seems to be used to discard values before a return in a "for" loop
        discard_top        ::= ROT_TWO POP_TOP
        discard_tops       ::= discard_top+

        return             ::= return_expr
                               discard_tops RETURN_VALUE

        return             ::= popb_return
        return             ::= pop_return
        return             ::= pop_ex_return
        except_stmt        ::= pop_ex_return
        pop_return         ::= POP_TOP return_expr RETURN_VALUE
        popb_return        ::= return_expr POP_BLOCK RETURN_VALUE
        pop_ex_return      ::= return_expr ROT_FOUR POP_EXCEPT RETURN_VALUE

        # 3.8 can push a looping JUMP_BACK into into a JUMP_ from a statement that jumps to it
        lastl_stmt         ::= ifpoplaststmtl
        ifpoplaststmtl     ::= testexpr POP_TOP c_stmts_opt
        ifelsestmtl        ::= testexpr c_stmts_opt jb_cfs else_suitel JUMP_BACK come_froms

        # Keep indices the same in ifelsestmtl
        cf_pt              ::= COME_FROM POP_TOP
        ifelsestmtl        ::= testexpr c_stmts cf_pt else_suite

        for38              ::= expr get_iter store for_block JUMP_BACK
        for38              ::= expr get_for_iter store for_block JUMP_BACK
        for38              ::= expr get_for_iter store for_block JUMP_BACK POP_BLOCK
        for38              ::= expr get_for_iter store for_block

        forelsestmt38      ::= expr get_for_iter store for_block POP_BLOCK else_suite
        forelsestmt38      ::= expr get_for_iter store for_block JUMP_BACK _come_froms else_suite

        forelselaststmt38  ::= expr get_for_iter store for_block POP_BLOCK else_suitec
        forelselaststmtl38 ::= expr get_for_iter store for_block POP_BLOCK else_suitel

        returns_in_except   ::= _stmts except_return_value
        except_return_value ::= POP_BLOCK return
        except_return_value ::= expr POP_BLOCK RETURN_VALUE

        whilestmt38        ::= _come_froms testexpr l_stmts_opt COME_FROM JUMP_BACK POP_BLOCK
        whilestmt38        ::= _come_froms testexpr l_stmts_opt JUMP_BACK POP_BLOCK
        whilestmt38        ::= _come_froms testexpr l_stmts_opt JUMP_BACK come_froms
        whilestmt38        ::= _come_froms testexpr returns               POP_BLOCK
        whilestmt38        ::= _come_froms testexpr l_stmts     JUMP_BACK
        whilestmt38        ::= _come_froms testexpr l_stmts     come_froms

        # while1elsestmt   ::=          l_stmts     JUMP_BACK
        whileTruestmt      ::= _come_froms l_stmts              JUMP_BACK POP_BLOCK
        while1stmt         ::= _come_froms l_stmts COME_FROM JUMP_BACK COME_FROM_LOOP
        whileTruestmt38    ::= _come_froms l_stmts JUMP_BACK
        whileTruestmt38    ::= _come_froms l_stmts JUMP_BACK COME_FROM_EXCEPT_CLAUSE
        whileTruestmt38    ::= _come_froms pass JUMP_BACK

        for_block          ::= _come_froms l_stmts_opt _come_from_loops JUMP_BACK

        except_cond1       ::= DUP_TOP expr COMPARE_OP jmp_false
                               POP_TOP POP_TOP POP_TOP
                               POP_EXCEPT
        except_cond_as     ::= DUP_TOP expr COMPARE_OP POP_JUMP_IF_FALSE
                               POP_TOP STORE_FAST POP_TOP

        try_elsestmtl38    ::= SETUP_FINALLY suite_stmts_opt POP_BLOCK
                               except_handler38 COME_FROM
                               else_suitel opt_come_from_except
        try_except         ::= SETUP_FINALLY suite_stmts_opt POP_BLOCK
                               except_handler38

        try_except38       ::= SETUP_FINALLY POP_BLOCK POP_TOP suite_stmts_opt
                               except_handler38a

        # suite_stmts has a return
        try_except38       ::= SETUP_FINALLY POP_BLOCK suite_stmts
                               except_handler38b
        try_except38r      ::= SETUP_FINALLY return_except
                               except_handler38b
        return_except      ::= stmts POP_BLOCK return


        # In 3.8 there seems to be some sort of code fiddle with POP_EXCEPT when there
        # is a final return in the "except" block.
        # So we treat the "return" separate from the other statements
        cond_except_stmt      ::= except_cond1 except_stmts
        cond_except_stmts_opt ::= cond_except_stmt*

        try_except38r2     ::= SETUP_FINALLY
                               suite_stmts_opt
                               POP_BLOCK JUMP_FORWARD
                               COME_FROM_FINALLY POP_TOP POP_TOP POP_TOP
                               cond_except_stmts_opt
                               POP_EXCEPT return
                               END_FINALLY
                               COME_FROM

        try_except38r3     ::= SETUP_FINALLY
                               suite_stmts_opt
                               POP_BLOCK JUMP_FORWARD
                               COME_FROM_FINALLY
                               cond_except_stmts_opt
                               POP_EXCEPT return
                               COME_FROM
                               END_FINALLY
                               COME_FROM


        try_except38r4     ::= SETUP_FINALLY
                               returns_in_except
                               COME_FROM_FINALLY
                               except_cond1
                               return
                               COME_FROM
                               END_FINALLY


        # suite_stmts has a return
        try_except38       ::= SETUP_FINALLY POP_BLOCK suite_stmts
                               except_handler38b
        try_except_as      ::= SETUP_FINALLY POP_BLOCK suite_stmts
                               except_handler_as END_FINALLY COME_FROM
        try_except_as      ::= SETUP_FINALLY suite_stmts
                               except_handler_as END_FINALLY COME_FROM

        try_except_ret38   ::= SETUP_FINALLY returns except_ret38a
        try_except_ret38a  ::= SETUP_FINALLY returns except_handler38c
                               END_FINALLY come_from_opt

        # Note: there is a suite_stmts_opt which seems
        # to be bookkeeping which is not expressed in source code
        except_ret38       ::= SETUP_FINALLY expr ROT_FOUR POP_BLOCK POP_EXCEPT
                               CALL_FINALLY RETURN_VALUE COME_FROM
                               COME_FROM_FINALLY
                               suite_stmts_opt END_FINALLY
        except_ret38a      ::= COME_FROM_FINALLY POP_TOP POP_TOP POP_TOP
                               expr ROT_FOUR
                               POP_EXCEPT RETURN_VALUE END_FINALLY

        except_handler38   ::= _jump COME_FROM_FINALLY
                               except_stmts END_FINALLY opt_come_from_except
        except_handler38a  ::= COME_FROM_FINALLY POP_TOP POP_TOP POP_TOP
                               POP_EXCEPT POP_TOP stmts END_FINALLY

        except_handler38c  ::= COME_FROM_FINALLY except_cond1a except_stmts
                               POP_EXCEPT JUMP_FORWARD COME_FROM
        except_handler_as  ::= COME_FROM_FINALLY except_cond_as tryfinallystmt
                               POP_EXCEPT JUMP_FORWARD COME_FROM

        tryfinallystmt     ::= SETUP_FINALLY suite_stmts_opt POP_BLOCK
                               BEGIN_FINALLY COME_FROM_FINALLY suite_stmts_opt
                               END_FINALLY


        lc_setup_finally   ::= LOAD_CONST SETUP_FINALLY
        call_finally_pt    ::= CALL_FINALLY POP_TOP
        cf_cf_finally      ::= come_from_opt COME_FROM_FINALLY
        pop_finally_pt     ::= POP_FINALLY POP_TOP
        ss_end_finally     ::= suite_stmts END_FINALLY
        sf_pb_call_returns ::= SETUP_FINALLY POP_BLOCK CALL_FINALLY returns


        # FIXME: DRY rules below
        tryfinally38rstmt  ::= sf_pb_call_returns
                               cf_cf_finally
                               ss_end_finally
        tryfinally38rstmt  ::= sf_pb_call_returns
                               cf_cf_finally END_FINALLY
                               suite_stmts
        tryfinally38rstmt  ::= sf_pb_call_returns
                               cf_cf_finally POP_FINALLY
                               ss_end_finally
        tryfinally38rstmt  ::= sf_bp_call_returns
                               COME_FROM_FINALLY POP_FINALLY
                               ss_end_finally

        tryfinally38rstmt2 ::= lc_setup_finally POP_BLOCK call_finally_pt
                               returns
                               cf_cf_finally pop_finally_pt
                               ss_end_finally POP_TOP
        tryfinally38rstmt3 ::= SETUP_FINALLY expr POP_BLOCK CALL_FINALLY RETURN_VALUE
                               COME_FROM COME_FROM_FINALLY
                               ss_end_finally

        tryfinally38stmt   ::= SETUP_FINALLY suite_stmts_opt POP_BLOCK
                               BEGIN_FINALLY COME_FROM_FINALLY
                               POP_FINALLY suite_stmts_opt END_FINALLY

        tryfinally38astmt  ::= LOAD_CONST SETUP_FINALLY suite_stmts_opt POP_BLOCK
                               BEGIN_FINALLY COME_FROM_FINALLY
                               POP_FINALLY POP_TOP suite_stmts_opt END_FINALLY POP_TOP
        """

    def p_38walrus(self, args):
        """
        # named_expr is also known as the "walrus op" :=
        expr              ::= named_expr
        named_expr        ::= expr DUP_TOP store
        """

    def __init__(self, debug_parser=PARSER_DEFAULT_DEBUG):
        super(Python38Parser, self).__init__(debug_parser)
        self.customized = {}

    def remove_rules_38(self):
        self.remove_rules(
            """
           stmt               ::= async_for_stmt37
           stmt               ::= for
           stmt               ::= forelsestmt
           stmt               ::= try_except36
           stmt               ::= async_forelse_stmt

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
           async_for_stmt37   ::= setup_loop expr
                                  GET_AITER
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

           for                ::= setup_loop expr get_for_iter store for_block POP_BLOCK
           for                ::= setup_loop expr get_for_iter store for_block POP_BLOCK NOP

           for_block          ::= l_stmts_opt COME_FROM_LOOP JUMP_BACK
           forelsestmt        ::= setup_loop expr get_for_iter store for_block POP_BLOCK else_suite
           forelselaststmt    ::= setup_loop expr get_for_iter store for_block POP_BLOCK else_suitec
           forelselaststmtl   ::= setup_loop expr get_for_iter store for_block POP_BLOCK else_suitel

           tryelsestmtl3      ::= SETUP_EXCEPT suite_stmts_opt POP_BLOCK
                                  except_handler COME_FROM else_suitel
                                  opt_come_from_except
           try_except         ::= SETUP_EXCEPT suite_stmts_opt POP_BLOCK
                                  except_handler opt_come_from_except
           tryfinallystmt     ::= SETUP_FINALLY suite_stmts_opt POP_BLOCK
                                  LOAD_CONST COME_FROM_FINALLY suite_stmts_opt
                                  END_FINALLY
           tryfinally36       ::= SETUP_FINALLY returns
                                  COME_FROM_FINALLY suite_stmts_opt END_FINALLY
           tryfinally_return_stmt ::= SETUP_FINALLY suite_stmts_opt POP_BLOCK
                                      LOAD_CONST COME_FROM_FINALLY
        """
        )

    def customize_grammar_rules(self, tokens, customize):
        super(Python37Parser, self).customize_grammar_rules(tokens, customize)
        self.remove_rules_38()
        self.check_reduce["whileTruestmt38"] = "tokens"
        self.check_reduce["whilestmt38"] = "tokens"
        self.check_reduce["try_elsestmtl38"] = "AST"

        # For a rough break out on the first word. This may
        # include instructions that don't need customization,
        # but we'll do a finer check after the rough breakout.
        customize_instruction_basenames = frozenset(
            (
                "BEFORE",
                "BUILD",
                "CALL",
                "DICT",
                "GET",
                "FORMAT",
                "LIST",
                "LOAD",
                "MAKE",
                "SETUP",
                "UNPACK",
            )
        )

        # Opcode names in the custom_ops_processed set have rules that get added
        # unconditionally and the rules are constant. So they need to be done
        # only once and if we see the opcode a second we don't have to consider
        # adding more rules.
        #
        custom_ops_processed = frozenset()

        # A set of instruction operation names that exist in the token stream.
        # We use this customize the grammar that we create.
        # 2.6-compatible set comprehensions
        self.seen_ops = frozenset([t.kind for t in tokens])
        self.seen_op_basenames = frozenset(
            [opname[: opname.rfind("_")] for opname in self.seen_ops]
        )

        custom_ops_processed = set(["DICT_MERGE"])

        # Loop over instructions adding custom grammar rules based on
        # a specific instruction seen.

        if "PyPy" in customize:
            self.addRule(
                """
              stmt ::= assign3_pypy
              stmt ::= assign2_pypy
              assign3_pypy       ::= expr expr expr store store store
              assign2_pypy       ::= expr expr store store
              """,
                nop_func,
            )

        n = len(tokens)
        # Determine if we have an iteration CALL_FUNCTION_1.
        has_get_iter_call_function1 = False
        for i, token in enumerate(tokens):
            if (
                token == "GET_ITER"
                and i < n - 2
                and tokens[i + 1] == "CALL_FUNCTION_1"
            ):
                has_get_iter_call_function1 = True

        for i, token in enumerate(tokens):
            opname = token.kind

            # Do a quick breakout before testing potentially
            # each of the dozen or so instruction in if elif.
            if (
                opname[: opname.find("_")] not in customize_instruction_basenames
                or opname in custom_ops_processed
            ):
                continue

            opname_base = opname[: opname.rfind("_")]

            # Do a quick breakout before testing potentially
            # each of the dozen or so instruction in if elif.
            if (
                opname[: opname.find("_")] not in customize_instruction_basenames
                or opname in custom_ops_processed
            ):
                continue
            if opname_base in (
                "BUILD_LIST",
                "BUILD_SET",
                "BUILD_SET_UNPACK",
                "BUILD_TUPLE",
                "BUILD_TUPLE_UNPACK",
            ):
                v = token.attr

                is_LOAD_CLOSURE = False
                if opname_base == "BUILD_TUPLE":
                    # If is part of a "load_closure", then it is not part of a
                    # "list".
                    is_LOAD_CLOSURE = True
                    for j in range(v):
                        if tokens[i - j - 1].kind != "LOAD_CLOSURE":
                            is_LOAD_CLOSURE = False
                            break
                    if is_LOAD_CLOSURE:
                        rule = "load_closure ::= %s%s" % (("LOAD_CLOSURE " * v), opname)
                        self.add_unique_rule(rule, opname, token.attr, customize)

                elif opname_base == "BUILD_LIST":
                    v = token.attr
                    if v == 0:
                        rule_str = """
                           list        ::= BUILD_LIST_0
                           list_unpack ::= BUILD_LIST_0 expr LIST_EXTEND
                           list        ::= list_unpack
                        """
                        self.add_unique_doc_rules(rule_str, customize)

                elif opname == "BUILD_TUPLE_UNPACK_WITH_CALL":
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

                if not is_LOAD_CLOSURE or v == 0:
                    # We do this complicated test to speed up parsing of
                    # pathelogically long literals, especially those over 1024.
                    build_count = token.attr
                    thousands = build_count // 1024
                    thirty32s = (build_count // 32) % 32
                    if thirty32s > 0:
                        rule = "expr32 ::=%s" % (" expr" * 32)
                        self.add_unique_rule(rule, opname_base, build_count, customize)
                        pass
                    if thousands > 0:
                        self.add_unique_rule(
                            "expr1024 ::=%s" % (" expr32" * 32),
                            opname_base,
                            build_count,
                            customize,
                        )
                        pass
                    collection = opname_base[opname_base.find("_") + 1 :].lower()
                    rule = (
                        ("%s ::= " % collection)
                        + "expr1024 " * thousands
                        + "expr32 " * thirty32s
                        + "expr " * (build_count % 32)
                        + opname
                    )
                    self.add_unique_rules(["expr ::= %s" % collection, rule], customize)
                    continue
                continue

            elif opname == "BUILD_STRING_2":
               self.addRule(
                   """
                     expr                  ::= formatted_value_debug
                     formatted_value_debug ::= LOAD_STR formatted_value2 BUILD_STRING_2
                     formatted_value_debug ::= LOAD_STR formatted_value1 BUILD_STRING_2
                   """,
                   nop_func,
               )
               custom_ops_processed.add(opname)

            elif opname == "BUILD_STRING_3":
               self.addRule(
                   """
                     expr                  ::= formatted_value_debug
                     formatted_value_debug ::= LOAD_STR formatted_value2 LOAD_STR BUILD_STRING_3
                     formatted_value_debug ::= LOAD_STR formatted_value1 LOAD_STR BUILD_STRING_3
                   """,
                   nop_func,
               )
               custom_ops_processed.add(opname)

            elif opname == "LOAD_CLOSURE":
                self.addRule("""load_closure ::= LOAD_CLOSURE+""", nop_func)

            elif opname == "LOOKUP_METHOD":
                # A PyPy speciality - DRY with parse3
                self.addRule(
                    """
                             expr      ::= attribute
                             attribute ::= expr LOOKUP_METHOD
                             """,
                    nop_func,
                )
                custom_ops_processed.add(opname)

            elif opname == "MAKE_FUNCTION_8":
                if "LOAD_DICTCOMP" in self.seen_ops:
                    # Is there something general going on here?
                    rule = """
                       dict_comp ::= load_closure LOAD_DICTCOMP LOAD_STR
                                     MAKE_FUNCTION_8 expr
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





    def reduce_is_invalid(self, rule, ast, tokens, first, last):
        invalid = super(Python38Parser,
                        self).reduce_is_invalid(rule, ast,
                                                tokens, first, last)
        self.remove_rules_38()
        if invalid:
            return invalid
        lhs = rule[0]
        if lhs in ("whileTruestmt38", "whilestmt38"):
            jb_index = last - 1
            while jb_index > 0 and tokens[jb_index].kind.startswith("COME_FROM"):
                jb_index -= 1
            t = tokens[jb_index]
            if t.kind != "JUMP_BACK":
                return True
            return t.attr != tokens[first].off2int()
            pass

        return False


class Python38ParserSingle(Python38Parser, PythonParserSingle):
    pass


if __name__ == "__main__":
    # Check grammar
    # FIXME: DRY this with other parseXX.py routines
    p = Python38Parser()
    p.remove_rules_38()
    p.check_grammar()
    from xdis.version_info import PYTHON_VERSION_TRIPLE, IS_PYPY

    if PYTHON_VERSION_TRIPLE[:2] == (3, 8):
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
