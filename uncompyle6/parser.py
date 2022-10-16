#  Copyright (c) 2015-2022 Rocky Bernstein
#  Copyright (c) 2005 by Dan Pascu <dan@windowmaker.org>
#  Copyright (c) 2000-2002 by hartmut Goebel <h.goebel@crazy-compilers.com>
#  Copyright (c) 1999 John Aycock
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
Common uncompyle6 parser routines.
"""

import sys

from spark_parser import GenericASTBuilder, DEFAULT_DEBUG as PARSER_DEFAULT_DEBUG
from uncompyle6.show import maybe_show_asm
from xdis import iscode


class ParserError(Exception):
    def __init__(self, token, offset, debug=PARSER_DEFAULT_DEBUG):
        self.token = token
        self.offset = offset
        self.debug = debug

    def __str__(self):
        return "Parse error at or near `%r' instruction at offset %s\n" % (
            self.token,
            self.offset,
        )


def nop_func(self, args):
    return None


class PythonParser(GenericASTBuilder):
    def __init__(self, SyntaxTree, start, debug):
        super(PythonParser, self).__init__(SyntaxTree, start, debug)
        # FIXME: customize per python parser version

        # These are the non-terminals we should collect into a list.
        # For example instead of:
        #   stmts -> stmts stmt -> stmts stmt stmt ...
        # collect as stmts -> stmt stmt ...
        nt_list = [
            "_come_froms",
            "_stmts",
            "attributes",
            "add_consts",
            "come_froms",
            "except_stmts",
            "exprlist",
            "importlist",
            "key_value_pairs",
            "kvlist",
            "kwargs",
            "l_stmts",
            "stmts",
            # Python < 3
            "print_items",
            # PyPy:
            "imports_cont",
            "kvlist_n",
            # Python 3.6+
            "come_from_loops",
            # Python 3.7+
            "importlist37",
            # Python < 1.4
            "args_store",
        ]
        self.collect = frozenset(nt_list)

        # For these items we need to keep the 1st epslion reduction since
        # the nonterminal name is used in a semantic action.
        self.keep_epsilon = frozenset(("kvlist_n", "kvlist"))

        # ??? Do we need a debug option to skip eliding singleton reductions?
        # Time will tell if it if useful in debugging

        # FIXME: optional_nt is a misnomer. It's really about there being a
        # singleton reduction that we can simplify. It also happens to be optional
        # in its other derivation
        self.optional_nt |= frozenset(
            ("come_froms", "suite_stmts", "l_stmts_opt", "c_stmts_opt", "stmts_opt", "stmt")
        )

        # Reduce singleton reductions in these nonterminals:
        # FIXME: would love to do expr, sstmts, stmts and
        # so on but that would require major changes to the
        # semantic actions
        self.singleton = frozenset(
            ("str", "store", "_stmts", "suite_stmts_opt", "inplace_op", "add_value")
        )
        # Instructions filled in from scanner
        self.insts = []

    def ast_first_offset(self, ast):
        if hasattr(ast, "offset"):
            return ast.offset
        else:
            return self.ast_first_offset(ast[0])

    def add_unique_rule(self, rule, opname, arg_count, customize):
        """Add rule to grammar, but only if it hasn't been added previously
           opname and stack_count are used in the customize() semantic
           the actions to add the semantic action rule. Stack_count is
           used in custom opcodes like MAKE_FUNCTION to indicate how
           many arguments it has. Often it is not used.
        """
        if rule not in self.new_rules:
            # print("XXX ", rule) # debug
            self.new_rules.add(rule)
            self.addRule(rule, nop_func)
            customize[opname] = arg_count
            pass
        return

    def add_unique_rules(self, rules, customize):
        """Add rules (a list of string) to grammar. Note that
        the rules must not be those that set arg_count in the
        custom dictionary.
        """
        for rule in rules:
            if len(rule) == 0:
                continue
            opname = rule.split("::=")[0].strip()
            self.add_unique_rule(rule, opname, 0, customize)
        return

    def add_unique_doc_rules(self, rules_str, customize):
        """Add rules (a docstring-like list of rules) to grammar.
        Note that the rules must not be those that set arg_count in the
        custom dictionary.
        """
        rules = [r.strip() for r in rules_str.split("\n")]
        self.add_unique_rules(rules, customize)
        return

    def cleanup(self):
        """
        Remove recursive references to allow garbage
        collector to collect this object.
        """
        for dict in (self.rule2func, self.rules, self.rule2name):
            for i in list(dict.keys()):
                dict[i] = None
        for i in dir(self):
            setattr(self, i, None)

    def debug_reduce(self, rule, tokens, parent, last_token_pos):
        """Customized format and print for our kind of tokens
        which gets called in debugging grammar reduce rules
        """

        def fix(c):
            s = str(c)
            last_token_pos = s.find("_")
            if last_token_pos == -1:
                return s
            else:
                return s[:last_token_pos]

        prefix = ""
        if parent and tokens:
            p_token = tokens[parent]
            if hasattr(p_token, "linestart") and p_token.linestart:
                prefix = "L.%3d: " % p_token.linestart
            else:
                prefix = "       "
            if hasattr(p_token, "offset"):
                prefix += "%3s" % fix(p_token.offset)
                if len(rule[1]) > 1:
                    prefix += "-%-3s " % fix(tokens[last_token_pos - 1].offset)
                else:
                    prefix += "     "
        else:
            prefix = "               "

        print("%s%s ::= %s (%d)" % (prefix, rule[0], " ".join(rule[1]), last_token_pos))

    def error(self, instructions, index):
        # Find the last line boundary
        start, finish = -1, -1
        for start in range(index, -1, -1):
            if instructions[start].linestart:
                break
            pass
        for finish in range(index + 1, len(instructions)):
            if instructions[finish].linestart:
                break
            pass
        if start > 0:
            err_token = instructions[index]
            print("Instruction context:")
            for i in range(start, finish):
                if i != index:
                    indent = "   "
                else:
                    indent = "-> "
                print("%s%s" % (indent, instructions[i]))
            raise ParserError(err_token, err_token.offset, self.debug["reduce"])
        else:
            raise ParserError(None, -1, self.debug["reduce"])

    def get_pos_kw(self, token):
        """Return then the number of positional parameters and
        represented by the attr field of token"""
        # Low byte indicates number of positional paramters,
        # high byte number of keyword parameters
        args_pos = token.attr & 0xFF
        args_kw = (token.attr >> 8) & 0xFF
        return args_pos, args_kw

    def nonterminal(self, nt, args):
        n = len(args)

        # # Use this to find lots of singleton rule
        # if n == 1 and nt not in self.singleton:
        #     print("XXX", nt)

        if nt in self.collect and n > 1:
            #
            #  Collect iterated thingies together. That is rather than
            #  stmts -> stmts stmt -> stmts stmt -> ...
            #  stmms -> stmt stmt ...
            #
            if not hasattr(args[0], "append"):
                # Was in self.optional_nt as a single item, but we find we have
                # more than one now...
                rv = GenericASTBuilder.nonterminal(self, nt, [args[0]])
            else:
                rv = args[0]
                pass
            # In a  list-like entity where the first item goes to epsilon,
            # drop that and save the 2nd item as the first one
            if len(rv) == 0 and nt not in self.keep_epsilon:
                rv = args[1]
            else:
                rv.append(args[1])
        elif n == 1 and args[0] in self.singleton:
            rv = GenericASTBuilder.nonterminal(self, nt, args[0])
            del args[0]  # save memory
        elif n == 1 and nt in self.optional_nt:
            rv = args[0]
        else:
            rv = GenericASTBuilder.nonterminal(self, nt, args)
        return rv

    def __ambiguity(self, children):
        # only for debugging! to be removed hG/2000-10-15
        print(children)
        return GenericASTBuilder.ambiguity(self, children)

    def resolve(self, list):
        if len(list) == 2 and "function_def" in list and "assign" in list:
            return "function_def"
        if "grammar" in list and "expr" in list:
            return "expr"
        # print >> sys.stderr, 'resolve', str(list)
        return GenericASTBuilder.resolve(self, list)

    ###############################################
    #  Common Python 2 and Python 3 grammar rules #
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

    def p_stmt(self, args):
        """
        pass ::=

        _stmts ::= stmt+

        # statements with continue
        c_stmts ::= _stmts
        c_stmts ::= _stmts lastc_stmt
        c_stmts ::= lastc_stmt
        c_stmts ::= continues

        lastc_stmt ::= iflaststmt
        lastc_stmt ::= forelselaststmt
        lastc_stmt ::= ifelsestmtc

        c_stmts_opt ::= c_stmts
        c_stmts_opt ::= pass

        stmts_opt ::= _stmts
        stmts_opt ::= pass

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

        stmt ::= assert

        stmt ::= classdef
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
        stmt ::= with
        stmt ::= withasstmt

        stmt   ::= delete
        delete ::= DELETE_FAST
        delete ::= DELETE_NAME
        delete ::= DELETE_GLOBAL


        stmt   ::= return
        return ::= return_expr RETURN_VALUE

        # "returns" nonterminal is a sequence of statements that ends in a RETURN statement.
        # In later Python versions with jump optimization, this can cause JUMPs
        # that would normally appear to be omitted.

        returns ::= return
        returns ::= _stmts return

        """
        pass

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
        """
        expr ::= generator_exp
        stmt ::= genexpr_func

        genexpr_func ::= LOAD_FAST FOR_ITER store comp_iter JUMP_BACK
        """

    def p_jump(self, args):
        """
        _jump ::= JUMP_ABSOLUTE
        _jump ::= JUMP_FORWARD
        _jump ::= JUMP_BACK

        # Zero or more COME_FROMs - loops can have this
        _come_froms ::= COME_FROM*

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
        for_iter ::= GET_ITER FOR_ITER

        for_block ::= l_stmts_opt _come_froms JUMP_BACK

        forelsestmt ::= SETUP_LOOP expr for_iter store
                        for_block POP_BLOCK else_suite _come_froms

        forelselaststmt ::= SETUP_LOOP expr for_iter store
                for_block POP_BLOCK else_suitec _come_froms

        forelselaststmtl ::= SETUP_LOOP expr for_iter store
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
        import_from      ::= LOAD_CONST LOAD_CONST IMPORT_NAME importlist POP_TOP
        importmultiple   ::= LOAD_CONST LOAD_CONST alias imports_cont

        imports_cont ::= import_cont+
        import_cont  ::= LOAD_CONST LOAD_CONST alias

        attributes   ::= LOAD_ATTR+
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

    def p_set_comp(self, args):
        """
        comp_iter ::= comp_for
        comp_iter ::= comp_body
        comp_body ::= gen_comp_body
        gen_comp_body ::= expr YIELD_VALUE POP_TOP

        comp_iter ::= comp_if
        comp_if  ::= expr jmp_false comp_iter
        """

    def p_expr(self, args):
        """
        expr ::= LOAD_CODE
        expr ::= LOAD_CONST
        expr ::= LOAD_DEREF
        expr ::= LOAD_FAST
        expr ::= LOAD_GLOBAL
        expr ::= LOAD_NAME
        expr ::= _lambda_body
        expr ::= and
        expr ::= bin_op
        expr ::= call
        expr ::= compare
        expr ::= dict
        expr ::= list
        expr ::= or
        expr ::= subscript
        expr ::= subscript2
        expr ::= unary_op
        expr ::= unary_not
        expr ::= yield

        # bin_op (formerly "binary_expr") is the Python AST BinOp
        bin_op ::= expr expr binary_operator
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

        # unary_op (formerly "unary_expr") is the Python AST BinOp
        unary_op          ::= expr unary_operator
        unary_operator    ::= UNARY_POSITIVE
        unary_operator    ::= UNARY_NEGATIVE
        unary_operator    ::= UNARY_INVERT

        unary_not ::= expr UNARY_NOT

        subscript ::= expr expr BINARY_SUBSCR

        attribute ::= expr LOAD_ATTR
        get_iter  ::= expr GET_ITER

        yield ::= expr YIELD_VALUE

        _lambda_body ::= lambda_body

        expr ::= if_exp

        return_expr ::= expr
        return_expr ::= ret_and
        return_expr ::= ret_or

        return_expr_or_cond ::= return_expr
        return_expr_or_cond ::= if_exp_ret

        stmt ::= return_expr_lambda

        return_expr_lambda ::= return_expr RETURN_VALUE_LAMBDA LAMBDA_MARKER
        return_expr_lambda ::= return_expr RETURN_VALUE_LAMBDA

        compare        ::= compare_chained
        compare        ::= compare_single
        compare_single ::= expr expr COMPARE_OP

        # A compare_chained is two comparisions like x <= y <= z
        compare_chained  ::= expr compare_chained1 ROT_TWO POP_TOP _come_froms
        compare_chained2 ::= expr COMPARE_OP JUMP_FORWARD

        # Non-null kvlist items are broken out in the indiviual grammars
        kvlist ::=

        # Positional arguments in make_function
        pos_arg ::= expr
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


def parse(p, tokens, customize, code):
    p.customize_grammar_rules(tokens, customize)
    ast = p.parse(tokens)
    #  p.cleanup()
    return ast


def get_python_parser(
    version, debug_parser=PARSER_DEFAULT_DEBUG, compile_mode="exec", is_pypy=False
):
    """Returns parser object for Python version 2 or 3, 3.2, 3.5on,
    etc., depending on the parameters passed.  *compile_mode* is either
    'exec', 'eval', or 'single'. See
    https://docs.python.org/3.6/library/functions.html#compile for an
    explanation of the different modes.
    """

    # If version is a string, turn that into the corresponding float.
    if isinstance(version, str):
        version = tuple([int(v) for v in version.split(".")[:2]])

    version = version[:2]

    # FIXME: there has to be a better way...
    # We could do this as a table lookup, but that would force us
    # in import all of the parsers all of the time. Perhaps there is
    # a lazy way of doing the import?

    if version < (3, 0):
        if version < (2, 2):
            if version == (1, 0):
                import uncompyle6.parsers.parse10 as parse10

                if compile_mode == "exec":
                    p = parse10.Python10Parser(debug_parser)
                else:
                    p = parse10.Python01ParserSingle(debug_parser)
            elif version == (1, 1):
                import uncompyle6.parsers.parse11 as parse11

                if compile_mode == "exec":
                    p = parse11.Python11Parser(debug_parser)
                else:
                    p = parse11.Python11ParserSingle(debug_parser)
            if version == (1, 2):
                import uncompyle6.parsers.parse12 as parse12

                if compile_mode == "exec":
                    p = parse12.Python12Parser(debug_parser)
                else:
                    p = parse12.Python12ParserSingle(debug_parser)
            if version == (1, 3):
                import uncompyle6.parsers.parse13 as parse13

                if compile_mode == "exec":
                    p = parse13.Python13Parser(debug_parser)
                else:
                    p = parse13.Python13ParserSingle(debug_parser)
            elif version == (1, 4):
                import uncompyle6.parsers.parse14 as parse14

                if compile_mode == "exec":
                    p = parse14.Python14Parser(debug_parser)
                else:
                    p = parse14.Python14ParserSingle(debug_parser)
            elif version == (1, 5):
                import uncompyle6.parsers.parse15 as parse15

                if compile_mode == "exec":
                    p = parse15.Python15Parser(debug_parser)
                else:
                    p = parse15.Python15ParserSingle(debug_parser)
            elif version == (1, 6):
                import uncompyle6.parsers.parse16 as parse16

                if compile_mode == "exec":
                    p = parse16.Python16Parser(debug_parser)
                else:
                    p = parse16.Python16ParserSingle(debug_parser)
            elif version == (2, 1):
                import uncompyle6.parsers.parse21 as parse21

                if compile_mode == "exec":
                    p = parse21.Python21Parser(debug_parser)
                else:
                    p = parse21.Python21ParserSingle(debug_parser)
        elif version == (2, 2):
            import uncompyle6.parsers.parse22 as parse22

            if compile_mode == "exec":
                p = parse22.Python22Parser(debug_parser)
            else:
                p = parse22.Python22ParserSingle(debug_parser)
        elif version == (2, 3):
            import uncompyle6.parsers.parse23 as parse23

            if compile_mode == "exec":
                p = parse23.Python23Parser(debug_parser)
            else:
                p = parse23.Python23ParserSingle(debug_parser)
        elif version == (2, 4):
            import uncompyle6.parsers.parse24 as parse24

            if compile_mode == "exec":
                p = parse24.Python24Parser(debug_parser)
            else:
                p = parse24.Python24ParserSingle(debug_parser)
        elif version == (2, 5):
            import uncompyle6.parsers.parse25 as parse25

            if compile_mode == "exec":
                p = parse25.Python25Parser(debug_parser)
            else:
                p = parse25.Python25ParserSingle(debug_parser)
        elif version == (2, 6):
            import uncompyle6.parsers.parse26 as parse26

            if compile_mode == "exec":
                p = parse26.Python26Parser(debug_parser)
            else:
                p = parse26.Python26ParserSingle(debug_parser)
        elif version == (2, 7):
            import uncompyle6.parsers.parse27 as parse27

            if compile_mode == "exec":
                p = parse27.Python27Parser(debug_parser)
            else:
                p = parse27.Python27ParserSingle(debug_parser)
        else:
            import uncompyle6.parsers.parse2 as parse2

            if compile_mode == "exec":
                p = parse2.Python2Parser(debug_parser)
            else:
                p = parse2.Python2ParserSingle(debug_parser)
                pass
            pass
        pass
    else:
        import uncompyle6.parsers.parse3 as parse3

        if version == (3, 0):
            import uncompyle6.parsers.parse30 as parse30

            if compile_mode == "exec":
                p = parse30.Python30Parser(debug_parser)
            else:
                p = parse30.Python30ParserSingle(debug_parser)
        elif version == (3, 1):
            import uncompyle6.parsers.parse31 as parse31

            if compile_mode == "exec":
                p = parse31.Python31Parser(debug_parser)
            else:
                p = parse31.Python31ParserSingle(debug_parser)
        elif version == (3, 2):
            import uncompyle6.parsers.parse32 as parse32

            if compile_mode == "exec":
                p = parse32.Python32Parser(debug_parser)
            else:
                p = parse32.Python32ParserSingle(debug_parser)
        elif version == (3, 3):
            import uncompyle6.parsers.parse33 as parse33

            if compile_mode == "exec":
                p = parse33.Python33Parser(debug_parser)
            else:
                p = parse33.Python33ParserSingle(debug_parser)
        elif version == (3, 4):
            import uncompyle6.parsers.parse34 as parse34

            if compile_mode == "exec":
                p = parse34.Python34Parser(debug_parser)
            else:
                p = parse34.Python34ParserSingle(debug_parser)
        elif version == (3, 5):
            import uncompyle6.parsers.parse35 as parse35

            if compile_mode == "exec":
                p = parse35.Python35Parser(debug_parser)
            else:
                p = parse35.Python35ParserSingle(debug_parser)
        elif version == (3, 6):
            import uncompyle6.parsers.parse36 as parse36

            if compile_mode == "exec":
                p = parse36.Python36Parser(debug_parser)
            else:
                p = parse36.Python36ParserSingle(debug_parser)
        elif version == (3, 7):
            import uncompyle6.parsers.parse37 as parse37

            if compile_mode == "exec":
                p = parse37.Python37Parser(debug_parser)
            else:
                p = parse37.Python37ParserSingle(debug_parser)
        elif version == (3, 8):
            import uncompyle6.parsers.parse38 as parse38

            if compile_mode == "exec":
                p = parse38.Python38Parser(debug_parser)
            else:
                p = parse38.Python38ParserSingle(debug_parser)
        else:
            if compile_mode == "exec":
                p = parse3.Python3Parser(debug_parser)
            else:
                p = parse3.Python3ParserSingle(debug_parser)
    p.version = version
    # p.dump_grammar() # debug
    return p


class PythonParserSingle(PythonParser):
    def p_call_stmt_single(self, args):
        """
        # single-mode compilation. Eval-mode interactive compilation
        # drops the last rule.

        call_stmt ::= expr PRINT_EXPR
        """


def python_parser(
    version,
    co,
    out=sys.stdout,
    showasm=False,
    parser_debug=PARSER_DEFAULT_DEBUG,
    is_pypy=False,
):
    """
    Parse a code object to an abstract syntax tree representation.

    :param version:         The python version this code is from as a float, for
                            example 2.6, 2.7, 3.2, 3.3, 3.4, 3.5 etc.
    :param co:              The code object to parse.
    :param out:             File like object to write the output to.
    :param showasm:         Flag which determines whether the disassembled and
                            ingested code is written to sys.stdout or not.
    :param parser_debug:    dict containing debug flags for the spark parser.

    :return: Abstract syntax tree representation of the code object.
    """

    assert iscode(co)
    from uncompyle6.scanner import get_scanner

    scanner = get_scanner(version, is_pypy)
    tokens, customize = scanner.ingest(co)
    maybe_show_asm(showasm, tokens)

    # For heavy grammar debugging
    # parser_debug = {'rules': True, 'transition': True, 'reduce' : True,
    #                 'showstack': 'full'}

    p = get_python_parser(version, parser_debug)

    # FIXME: have p.insts update in a better way
    # modularity is broken here
    p.insts = scanner.insts
    p.offset2inst_index = scanner.offset2inst_index

    return parse(p, tokens, customize, co)


if __name__ == "__main__":

    def parse_test(co):
        from xdis.version_info import PYTHON_VERSION_TRIPLE, IS_PYPY

        ast = python_parser(PYTHON_VERSION_TRIPLE[:2], co, showasm=True, is_pypy=IS_PYPY)
        print(ast)
        return
    parse_test(parse_test.func_code)
