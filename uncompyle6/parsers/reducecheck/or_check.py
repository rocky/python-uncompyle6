#  Copyright (c) 2020 Rocky Bernstein

ASSERT_OPS = frozenset(["LOAD_ASSERT", "RAISE_VARARGS_1"])
def or_check(self, lhs, n, rule, ast, tokens, first, last):
    rhs = rule[1]

    # print("XXX", first, last, rule)
    # for t in range(first, last): print(tokens[t])
    # print("="*40)

    if rhs[0:2] in (("expr_jt", "expr"),
                    ("expr_jitop", "expr"),
                    ("expr_jit", "expr")):
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

        last_token = tokens[last]
        last_token_offset = last_token.off2int()

        # FIXME: use instructions for all of this
        if jmp_true_target < first_offset:
            return False
        elif jmp_true_target < last_token_offset:
            return True

        # If the jmp is backwards
        if last_token == "POP_JUMP_IF_FALSE" and not self.version[:2] in ((2, 7), (3, 5), (3, 6)):
            if last_token.attr < last_token_offset:
                # For a backwards loop, well compare to the instruction *after*
                # then POP_JUMP...
                last_token = tokens[last + 1]
            # HACK alert 3 is the Python < 3.6ish thing.
            # Convert to using instructions
            return not (
                (last_token_offset <= jmp_true_target <= last_token_offset + 3)
                or jmp_true_target < tokens[first].off2int()
            )
        elif last_token == "JUMP_FORWARD" and expr_jt.kind != "expr_jitop":
            # "or" has to fall through to the next statement
            # FIXME: use instructions for all of this
            return True


    return False
