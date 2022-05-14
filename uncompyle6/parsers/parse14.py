#  Copyright (c) 2018, 2022 Rocky Bernstein

from spark_parser import DEFAULT_DEBUG as PARSER_DEFAULT_DEBUG
from uncompyle6.parser import PythonParserSingle, nop_func
from uncompyle6.parsers.parse15 import Python15Parser

class Python14Parser(Python15Parser):

    def p_misc14(self, args):
        """
        # Not much here yet, but will probably need to add UNARY_CALL,
        # LOAD_LOCAL, SET_FUNC_ARGS

        args            ::= RESERVE_FAST UNPACK_ARG args_store
        args_store      ::= STORE_FAST*
        call            ::= expr tuple BINARY_CALL
        expr            ::= call
        kv              ::= DUP_TOP expr ROT_TWO LOAD_CONST STORE_SUBSCR
        mkfunc          ::= LOAD_CODE BUILD_FUNCTION
        print_expr_stmt ::= expr PRINT_EXPR
        raise_stmt2     ::= expr expr RAISE_EXCEPTION
        star_args       ::= RESERVE_FAST UNPACK_VARARG_1 args_store
        stmt            ::= args
        stmt            ::= print_expr_stmt
        stmt            ::= star_args
        stmt            ::= varargs
        varargs         ::= RESERVE_FAST UNPACK_VARARG_0 args_store

        # Not strictly needed, but tidies up output

        stmt     ::= doc_junk
        doc_junk ::= LOAD_CONST POP_TOP

        # Not sure why later Python's omit the COME_FROM
        jb_pop14  ::= JUMP_BACK COME_FROM POP_TOP

        whileelsestmt ::= SETUP_LOOP testexpr l_stmts_opt
                          jb_pop14
                          POP_BLOCK else_suitel COME_FROM

        print_items_nl_stmt ::= expr PRINT_ITEM_CONT print_items_opt PRINT_NEWLINE_CONT


        # 1.4 doesn't have linenotab, and although this shouldn't
        # be a show stopper, our CONTINUE detection is off here.
        continue ::= JUMP_BACK
        """

    def __init__(self, debug_parser=PARSER_DEFAULT_DEBUG):
        super(Python14Parser, self).__init__(debug_parser)
        self.customized = {}

    def customize_grammar_rules(self, tokens, customize):
        super(Python14Parser, self).customize_grammar_rules(tokens, customize)
        self.remove_rules("""
        whileelsestmt ::= SETUP_LOOP testexpr l_stmts_opt
                          jb_pop
                          POP_BLOCK else_suitel COME_FROM
        """)
        self.check_reduce["doc_junk"] = "tokens"
        for i, token in enumerate(tokens):
            opname = token.kind
            opname_base = opname[:opname.rfind("_")]

            if opname_base == "UNPACK_VARARG":
                if token.attr > 1:
                    self.addRule("star_args ::= RESERVE_FAST %s args_store" % opname, nop_func)


    def reduce_is_invalid(self, rule, ast, tokens, first, last):
        invalid = super(Python14Parser,
                        self).reduce_is_invalid(rule, ast,
                                                tokens, first, last)
        if invalid or tokens is None:
            return invalid
        if rule[0] == 'doc_junk':
            return not isinstance(tokens[first].pattr, str)



class Python14ParserSingle(Python14Parser, PythonParserSingle):
    pass

if __name__ == '__main__':
    # Check grammar
    p = Python14Parser()
    p.check_grammar()
    p.dump_grammar()

# local variables:
# tab-width: 4
