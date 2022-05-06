import re
from uncompyle6.parser import get_python_parser, python_parser
from uncompyle6.scanner import get_scanner
from xdis.version_info import PYTHON_VERSION_TRIPLE, IS_PYPY


def test_grammar():
    def check_tokens(tokens, opcode_set):
        remain_tokens = set(tokens) - opcode_set
        remain_tokens = set([re.sub(r"_\d+$", "", t) for t in remain_tokens])
        remain_tokens = set([re.sub("_CONT$", "", t) for t in remain_tokens])
        remain_tokens = set([re.sub("LOAD_CODE$", "", t) for t in remain_tokens])
        remain_tokens = set(remain_tokens) - opcode_set
        assert remain_tokens == set([]), "Remaining tokens %s\n====\n%s" % (
            remain_tokens,
            p.dump_grammar(),
        )

    p = get_python_parser(PYTHON_VERSION_TRIPLE, is_pypy=IS_PYPY)
    (lhs, rhs, tokens, right_recursive, dup_rhs) = p.check_sets()

    # We have custom rules that create the below
    expect_lhs = set(["pos_arg"])

    if PYTHON_VERSION_TRIPLE < (3, 8):
        if PYTHON_VERSION_TRIPLE < (3, 7):
            expect_lhs.add("attribute")

        expect_lhs.add("get_iter")

        if PYTHON_VERSION_TRIPLE >= (3, 8) or PYTHON_VERSION_TRIPLE < (3, 0):
            expect_lhs.add("stmts_opt")
    else:
        expect_lhs.add("async_with_as_stmt")
        expect_lhs.add("async_with_stmt")

    unused_rhs = set(["list", "mkfunc", "lambda_body", "unpack"])

    expect_right_recursive = set([("designList", ("store", "DUP_TOP", "designList"))])

    if PYTHON_VERSION_TRIPLE[:2] <= (3, 6):
        unused_rhs.add("call")

    if PYTHON_VERSION_TRIPLE >= (2, 7):
        expect_lhs.add("kvlist")
        expect_lhs.add("kv3")
        unused_rhs.add("dict")

        if PYTHON_VERSION_TRIPLE < (3, 7) and PYTHON_VERSION_TRIPLE[:2] != (2, 7):
            # NOTE: this may disappear
            expect_lhs.add("except_handler_else")

    expect_lhs.add("load_genexpr")

    unused_rhs = unused_rhs.union(
        set(
            """
    except_pop_except generator_exp
    """.split()
        )
    )
    if PYTHON_VERSION_TRIPLE < (3, 7):
        expect_lhs.add("annotate_arg")
        expect_lhs.add("annotate_tuple")
        unused_rhs.add("mkfunc_annotate")

    unused_rhs.add("dict_comp")
    unused_rhs.add("classdefdeco1")
    unused_rhs.add("tryelsestmtl")
    if PYTHON_VERSION_TRIPLE >= (3, 5):
        expect_right_recursive.add(
            (("l_stmts", ("lastl_stmt", "come_froms", "l_stmts")))
        )
        pass
    pass

    if PYTHON_VERSION_TRIPLE >= (3, 7):
        expect_lhs.add("set_for")
        unused_rhs.add("set_iter")
        pass
    pass
    # FIXME
    if PYTHON_VERSION_TRIPLE < (3, 8):
        assert expect_lhs == set(lhs)
        assert unused_rhs == set(rhs)

    assert expect_right_recursive == right_recursive

    expect_dup_rhs = frozenset(
        [
            ("COME_FROM",),
            ("CONTINUE",),
            ("JUMP_ABSOLUTE",),
            ("LOAD_CONST",),
            ("JUMP_BACK",),
            ("JUMP_FORWARD",),
        ]
    )
    reduced_dup_rhs = dict((k, dup_rhs[k]) for k in dup_rhs if k not in expect_dup_rhs)
    if reduced_dup_rhs:
        print("\nPossible duplicate RHS that might be folded, into one of the LHS symbols")
        for k in reduced_dup_rhs:
            print(k, reduced_dup_rhs[k])
    # assert not reduced_dup_rhs, reduced_dup_rhs

    s = get_scanner(PYTHON_VERSION_TRIPLE, IS_PYPY)
    ignore_set = set(
        """
            JUMP_BACK CONTINUE
            COME_FROM COME_FROM_EXCEPT
            COME_FROM_EXCEPT_CLAUSE
            COME_FROM_LOOP COME_FROM_WITH
            COME_FROM_FINALLY ELSE
            LOAD_GENEXPR LOAD_ASSERT LOAD_SETCOMP LOAD_DICTCOMP LOAD_STR LOAD_CODE
            LAMBDA_MARKER
            RETURN_END_IF RETURN_END_IF_LAMBDA RETURN_VALUE_LAMBDA RETURN_LAST
            """.split()
    )

    if (2, 6) <= PYTHON_VERSION_TRIPLE <= (2, 7):
        opcode_set = set(s.opc.opname).union(ignore_set)
        if PYTHON_VERSION_TRIPLE[:2] == (2, 6):
            opcode_set.add("THEN")
        check_tokens(tokens, opcode_set)
    elif PYTHON_VERSION_TRIPLE[:2] == (3, 4):
        ignore_set.add("LOAD_CLASSNAME")
        ignore_set.add("STORE_LOCALS")
        opcode_set = set(s.opc.opname).union(ignore_set)
        check_tokens(tokens, opcode_set)


def test_dup_rule():
    import inspect

    python_parser(
        PYTHON_VERSION_TRIPLE,
        inspect.currentframe().f_code,
        is_pypy=IS_PYPY,
        parser_debug={
            "dups": True,
            "transition": False,
            "reduce": False,
            "rules": False,
            "errorstack": None,
            "context": True,
        },
    )
