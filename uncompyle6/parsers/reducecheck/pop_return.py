#  Copyright (c) 2020 Rocky Bernstein


def pop_return_check(self, lhs, n, rule, ast, tokens, first, last):
    # If the first instruction of return_expr (the instruction after POP_TOP) is
    # has a linestart, then the POP_TOP was probably part of the previous
    # statement, such as a call() where the return value is discarded.
    return tokens[first + 1].linestart
