#  Copyright (c) 2015-2016 Rocky Bernstein
#  Copyright (c) 2005 by Dan Pascu <dan@windowmaker.org>
#  Copyright (c) 2000-2002 by hartmut Goebel <h.goebel@crazy-compilers.com>
#  Copyright (c) 1999 John Aycock
"""
Common uncompyle parser routines.
"""

from __future__ import print_function

import sys

from uncompyle6.code import iscode
from spark_parser import GenericASTBuilder, DEFAULT_DEBUG as PARSER_DEFAULT_DEBUG

class ParserError(Exception):
    def __init__(self, token, offset):
        self.token = token
        self.offset = offset

    def __str__(self):
        return "Syntax error at or near `%r' token at offset %s\n" % \
               (self.token, self.offset)

nop_func = lambda self, args: None

class PythonParser(GenericASTBuilder):

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

    def error(self, token):
            raise ParserError(token, token.offset)

    def typestring(self, token):
        return token.type

    def nonterminal(self, nt, args):
        collect = ('stmts', 'exprlist', 'kvlist', '_stmts', 'print_items')

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
        print(children)
        return GenericASTBuilder.ambiguity(self, children)

    def resolve(self, list):
        if len(list) == 2 and 'funcdef' in list and 'assign' in list:
            return 'funcdef'
        if 'grammar' in list and 'expr' in list:
            return 'expr'
        # print >> sys.stderr, 'resolve', str(list)
        return GenericASTBuilder.resolve(self, list)

    ##############################################
    ## Common Python 2 and Python 3 grammar rules
    ##############################################
    def p_start(self, args):
        '''
        # The start or goal symbol
        stmts ::= stmts sstmt
        stmts ::= sstmt
        '''

    def p_call_stmt(self, args):
        '''
        # eval-mode compilation.  Single-mode interactive compilation
        # adds another rule.
        call_stmt ::= expr POP_TOP
        '''

    def p_funcdef(self, args):
        '''
        stmt ::= funcdef
        funcdef ::= mkfunc designator
        stmt ::= funcdefdeco
        funcdefdeco ::= mkfuncdeco designator
        mkfuncdeco ::= expr mkfuncdeco CALL_FUNCTION_1
        mkfuncdeco ::= expr mkfuncdeco0 CALL_FUNCTION_1
        mkfuncdeco0 ::= mkfunc
        load_closure ::= load_closure LOAD_CLOSURE
        load_closure ::= LOAD_CLOSURE
        '''

    def p_genexpr(self, args):
        '''
        expr ::= genexpr

        genexpr ::= LOAD_GENEXPR MAKE_FUNCTION_0 expr GET_ITER CALL_FUNCTION_1

        stmt ::= genexpr_func

        genexpr_func ::= LOAD_FAST FOR_ITER designator comp_iter JUMP_BACK
        '''

    def p_dictcomp(self, args):
        '''
        expr ::= dictcomp
        dictcomp ::= LOAD_DICTCOMP MAKE_FUNCTION_0 expr GET_ITER CALL_FUNCTION_1
        stmt ::= dictcomp_func

        dictcomp_func ::= BUILD_MAP LOAD_FAST FOR_ITER designator
                comp_iter JUMP_BACK RETURN_VALUE RETURN_LAST

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

        stmt ::= assign2
        stmt ::= assign3
        assign2 ::= expr expr ROT_TWO designator designator
        assign3 ::= expr expr expr ROT_THREE ROT_TWO designator designator designator
        '''

    def p_import20(self, args):
        '''
        stmt ::= importstmt
        stmt ::= importfrom
        stmt ::= importstar
        stmt ::= importmultiple

        importlist2 ::= importlist2 import_as
        importlist2 ::= import_as
        import_as ::= IMPORT_NAME designator
        import_as ::= IMPORT_NAME load_attrs designator
        import_as ::= IMPORT_FROM designator

        importstmt ::= LOAD_CONST LOAD_CONST import_as
        importstar ::= LOAD_CONST LOAD_CONST IMPORT_NAME IMPORT_STAR
        importfrom ::= LOAD_CONST LOAD_CONST IMPORT_NAME importlist2 POP_TOP
        importstar ::= LOAD_CONST LOAD_CONST IMPORT_NAME_CONT IMPORT_STAR
        importfrom ::= LOAD_CONST LOAD_CONST IMPORT_NAME_CONT importlist2 POP_TOP
        importmultiple ::= LOAD_CONST LOAD_CONST import_as imports_cont

        imports_cont ::= imports_cont import_cont
        imports_cont ::= import_cont
        import_cont ::= LOAD_CONST LOAD_CONST import_as_cont
        import_as_cont ::= IMPORT_NAME_CONT designator
        import_as_cont ::= IMPORT_NAME_CONT load_attrs designator
        import_as_cont ::= IMPORT_FROM designator

        load_attrs ::= LOAD_ATTR
        load_attrs ::= load_attrs LOAD_ATTR
        '''

    def p_list_comprehension(self, args):
        """
        expr ::= list_compr
        list_compr ::= BUILD_LIST_0 list_iter

        list_iter ::= list_for
        list_iter ::= list_if
        list_iter ::= list_if_not
        list_iter ::= lc_body

        _come_from ::= COME_FROM
        _come_from ::=

        list_if ::= expr jmp_false list_iter
        list_if_not ::= expr jmp_true list_iter

        lc_body ::= expr LIST_APPEND
        """

    def p_setcomp(self, args):
        """
        expr ::= setcomp

        setcomp ::= LOAD_SETCOMP MAKE_FUNCTION_0 expr GET_ITER CALL_FUNCTION_1

        stmt ::= setcomp_func

        setcomp_func ::= BUILD_SET_0 LOAD_FAST FOR_ITER designator comp_iter
                JUMP_BACK RETURN_VALUE RETURN_LAST

        comp_iter ::= comp_if
        comp_iter ::= comp_ifnot
        comp_iter ::= comp_for
        comp_iter ::= comp_body
        comp_body ::= set_comp_body
        comp_body ::= gen_comp_body
        comp_body ::= dict_comp_body
        set_comp_body ::= expr SET_ADD
        gen_comp_body ::= expr YIELD_VALUE POP_TOP
        dict_comp_body ::= expr expr MAP_ADD

        comp_if ::= expr jmp_false comp_iter
        comp_ifnot ::= expr jmp_true comp_iter
        """


def parse(p, tokens, customize):
    p.add_custom_rules(tokens, customize)
    ast = p.parse(tokens)
    #  p.cleanup()
    return ast


def get_python_parser(version, debug_parser, compile_mode='exec'):
    """Returns parser object for Python version 2 or 3, 3.2, 3.5on,
    etc., depending on the parameters passed.  *compile_mode* is either
    'exec', 'eval', or 'single'. See
    https://docs.python.org/3.6/library/functions.html#compile for an
    explanation of the different modes.
    """

    if version < 3.0:
        import uncompyle6.parsers.parse2 as parse2
        if compile_mode == 'exec':
            p = parse2.Python2Parser(debug_parser)
        else:
            p = parse2.Python2ParserSingle(debug_parser)
    else:
        import uncompyle6.parsers.parse3 as parse3
        if version == 3.2:
            if compile_mode == 'exec':
                p = parse3.Python32Parser(debug_parser)
            else:
                p = parse3.Python32ParserSingle(debug_parser)
        elif version >= 3.5:
            if compile_mode == 'exec':
                p = parse3.Python35onParser(debug_parser)
            else:
                p = parse3.Python35onParserSingle(debug_parser)
        else:
            if compile_mode == 'exec':
                p = parse3.Python3Parser(debug_parser)
            else:
                p = parse3.Python3ParserSingle(debug_parser)
    p.version = version
    return p

class PythonParserSingle(PythonParser):
    def p_call_stmt(self, args):
        '''
        # single-mode compilation. Eval-mode interactive compilation
        # drops the last rule.

        call_stmt ::= expr POP_TOP
        call_stmt ::= expr PRINT_EXPR
        '''

def python_parser(version, co, out=sys.stdout, showasm=False,
                  parser_debug=PARSER_DEFAULT_DEBUG):
    assert iscode(co)
    from uncompyle6.scanner import get_scanner
    scanner = get_scanner(version)
    tokens, customize = scanner.disassemble(co)
    if showasm:
        for t in tokens:
            print(t)

    p = get_python_parser(version, parser_debug)
    return parse(p, tokens, customize)

if __name__ == '__main__':
    def parse_test(co):
        from uncompyle6 import PYTHON_VERSION
        ast = python_parser(PYTHON_VERSION, co, showasm=True)
        print(ast)
        return
    parse_test(parse_test.__code__)
