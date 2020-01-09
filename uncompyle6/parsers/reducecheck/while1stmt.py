#  Copyright (c) 2020 Rocky Bernstein


def while1stmt(self, lhs, n, rule, ast, tokens, first, last:

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

    for i in range(cfl - 1, first, -1):
        if tokens[i] != "POP_BLOCK":
            break
    if tokens[i].kind not in ("JUMP_BACK", "RETURN_VALUE", "RAISE_VARARGS_1"):
        if not tokens[i].kind.startswith("COME_FROM"):
            return True

    # Check that the SETUP_LOOP jumps to the offset after the
    # COME_FROM_LOOP
    if 0 <= last < n and tokens[last] in ("COME_FROM_LOOP", "JUMP_BACK"):
        # jump_back should be right before COME_FROM_LOOP?
        last += 1
    if last == n:
        last -= 1
    offset = tokens[last].off2int()
    assert tokens[first] == "SETUP_LOOP"
    # SETUP_LOOP location must jump either to the last token or the token after the last one
    return tokens[first].attr not in (offset, offset + 2)
