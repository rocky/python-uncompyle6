#  Copyright (c) 2020 Rocky Bernstein

from uncompyle6.scanners.tok import Token


def ifstmts_jump(self, lhs, n, rule, ast, tokens, first, last):

    if len(rule[1]) <= 1 or not ast:
        return False

    come_froms = ast[-1]
    # This is complicated, but note that the JUMP_IF instruction comes immediately
    # *before* _ifstmts_jump so that's what we have to test
    # the COME_FROM against. This can be complicated by intervening
    # POP_TOP, and pseudo COME_FROM, ELSE instructions
    #
    pop_jump_index = first - 1
    while pop_jump_index > 0 and tokens[pop_jump_index] in (
        "ELSE",
        "POP_TOP",
        "JUMP_FORWARD",
        "COME_FROM",
    ):
        pop_jump_index -= 1

    # FIXME: something is fishy when and EXTENDED ARG is needed before the
    # pop_jump_index instruction to get the argment. In this case, the
    # _ifsmtst_jump can jump to a spot beyond the come_froms.
    # That is going on in the non-EXTENDED_ARG case is that the POP_JUMP_IF
    # jumps to a JUMP_(FORWARD) which is changed into an EXTENDED_ARG POP_JUMP_IF
    # to the jumped forwarded address
    if tokens[pop_jump_index].attr > 256:
        return False

    pop_jump_offset = tokens[pop_jump_index].off2int(prefer_last=False)
    if isinstance(come_froms, Token):
        if (
            tokens[pop_jump_index].attr < pop_jump_offset and ast[0] != "pass"
        ):
            # This is a jump backwards to a loop. All bets are off here when there the
            # unless statement is "pass" which has no instructions associated with it.
            return False
        return (
            come_froms.attr is not None
            and pop_jump_offset > come_froms.attr
        )

    elif len(come_froms) == 0:
        return False
    else:
        return pop_jump_offset > come_froms[-1].attr
