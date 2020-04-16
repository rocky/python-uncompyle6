#  Copyright (c) 2020 Rocky Bernstein

ASSERT_OPS = frozenset(["LOAD_ASSERT", "RAISE_VARARGS_1"])
def or_check(self, lhs, n, rule, ast, tokens, first, last):
    rhs = rule[1]
    if rhs in (("expr_jt", "expr"),
               ("expr_jitop", "expr", "COME_FROM"),
               ("expr_jit", "expr", "\\e_come_from_opt")):
        if tokens[last] in  ASSERT_OPS or tokens[last-1] in ASSERT_OPS:
            return True

        # The following test is be the most accurate. It prevents "or" from being
        # mistake for part of an "assert".
        # There one might conceivably be "expr or AssertionError" code, but the
        # likelihood of that is vanishingly small.
        # The below then is useful until we get better control-flow analysis.
        # Note it is too hard in the scanner right nowto turn the LOAD_GLOBAL into
        # int LOAD_ASSERT, however in 3.9ish code generation does this by default.
        load_global = tokens[last - 1]
        if load_global == "LOAD_GLOBAL" and load_global.attr == "AssertionError":
            return True

        first_offset = tokens[first].off2int()
        expr_jt = ast[0]
        if expr_jt == "expr_jitop":
            jump_true = expr_jt[1]
        else:
            jump_true = expr_jt[1][0]

        jmp_true_target = jump_true.attr
        jmp_true_target < first_offset

        if jmp_true_target < first_offset:
            return False

        jmp_false = tokens[last]
        # If the jmp is backwards
        if jmp_false == "POP_JUMP_IF_FALSE":
            jmp_false_offset = jmp_false.off2int()
            if jmp_false.attr < jmp_false_offset:
                # For a backwards loop, well compare to the instruction *after*
                # then POP_JUMP...
                jmp_false = tokens[last + 1]
            return not (
                (jmp_false_offset <= jmp_true_target <= jmp_false_offset + 2)
                or jmp_true_target < tokens[first].off2int()
            )

    return False
