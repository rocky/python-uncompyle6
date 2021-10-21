#  Copyright (c) 2020-2021 Rocky Bernstein


def testtrue(self, lhs, n, rule, ast, tokens, first, last):
    # FIXME: make this work for all versions
    if self.version[:2] != (3, 7):
        return False
    if rule == ("testtrue", ("expr", "jmp_true")):
        pjit = tokens[min(last - 1, n - 2)]
        # If we have a backwards (looping) jump then this is
        # really a testfalse. "assert"s throw this off too.
        if pjit == "POP_JUMP_IF_TRUE" and tokens[first].off2int() > pjit.attr:
            assert_next = tokens[min(last + 1, n - 1)]
            return assert_next != "RAISE_VARARGS_1"
    elif rule == ("testfalsel", ("expr", "jmp_true")):
        pjit = tokens[min(last - 1, n - 2)]
        # If we have a backwards (looping) jump then this is
        # really a testtrue. But "asserts" work funny
        if pjit == "POP_JUMP_IF_TRUE" and tokens[first].off2int() > pjit.attr:
            assert_next = tokens[min(last + 1, n - 1)]
            return assert_next == "RAISE_VARARGS_1"
    return False
