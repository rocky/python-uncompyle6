#  Copyright (c) 2020, 2021, 2025 Rocky Bernstein
>>>>>>> python-3.0-to-3.2


def and_not_check(
    self, lhs, n, rule, ast, tokens, first, last
):
    jmp = ast[1]
    if jmp.kind.startswith("jmp_"):
        if last == n:
            return True
        jmp_target = jmp[0].attr

        if tokens[first].off2int() <= jmp_target < tokens[last].off2int():
            return True
        if rule == ("and_not", ("expr", "jmp_false", "expr", "POP_JUMP_IF_TRUE")):
            jmp2_target = ast[3].attr
            return jmp_target != jmp2_target
        return jmp_target != tokens[last].off2int()
    return False
