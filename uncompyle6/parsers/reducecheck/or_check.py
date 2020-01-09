#  Copyright (c) 2020 Rocky Bernstein


def or_check(self, lhs, n, rule, ast, tokens, first, last):
    if rule == ("or", ("expr", "jmp_true", "expr")):
        jmp_true_target = ast[1][0].attr
        jmp_false = tokens[last]
        # If the jmp is backwards
        if jmp_false == "POP_JUMP_IF_FALSE":
            if jmp_false.attr < jmp_false.off2int():
                # For a backwards loop, well compare to the instruction *after*
                # then POP_JUMP...
                jmp_false = tokens[last+1]
            return not (jmp_true_target == jmp_false.off2int() or
                        jmp_true_target < tokens[first].off2int())
        return tokens[last] in (
            "LOAD_ASSERT",
            "RAISE_VARARGS_1",
            )

    return False
