#  Copyright (c) 2020, 2022 Rocky Bernstein


def while1stmt(self, lhs, n, rule, ast, tokens, first, last):

    # If there is a fall through to the COME_FROM_LOOP, then this is
    # not a while 1. So the instruction before should either be a
    # JUMP_BACK or the instruction before should not be the target of a
    # jump. (Well that last clause i not quite right; that target could be
    # from dead code. Ugh. We need a more uniform control flow analysis.)
    if last == n or tokens[last - 1] == "COME_FROM_LOOP":
        cfl = last - 1
    else:
        cfl = last
    assert tokens[cfl] == "COME_FROM_LOOP"

    for loop_end in range(cfl - 1, first, -1):
        if tokens[loop_end] != "POP_BLOCK":
            break
    if tokens[loop_end].kind not in ("JUMP_BACK", "RETURN_VALUE", "RAISE_VARARGS_1"):
        if not tokens[loop_end].kind.startswith("COME_FROM"):
            return True
    # Check that the SETUP_LOOP jumps to the offset after the
    # COME_FROM_LOOP
    if 0 <= last and tokens[last] in ("COME_FROM_LOOP", "JUMP_BACK"):
        # jump_back should be right before COME_FROM_LOOP?
        last += 1
    if last == n:
        last -= 1
    offset = tokens[last].off2int()
    assert tokens[first] == "SETUP_LOOP"

    # Scan for jumps out of the loop. Skip the initial "SETUP_LOOP" instruction.
    # If there is a JUMP_BACK at the end, jumping to that is not breaking out
    # of the loop. However after that, any "POP_BLOCK"s or "COME_FROM_LOOP"s
    # are considered to break out of the loop.
    if tokens[loop_end] == "JUMP_BACK":
        loop_end += 1
    loop_end_offset = tokens[loop_end].off2int(prefer_last=False)
    for t in range(first + 1, loop_end):
        token = tokens[t]
        # token could be a pseudo-op like "LOAD_STR", which is not in
        # token.opc.  We will replace that with LOAD_CONST as an
        # example of an instruction that is not in token.opc.JUMP_OPS
        if token.opc.opmap.get(token.kind, "LOAD_CONST") in token.opc.JUMP_OPS:
            if token.attr >= loop_end_offset:
                return True

    # SETUP_LOOP location must jump either to the last token or the token after the last one
    return tokens[first].attr not in (offset, offset + 2)
