#  Copyright (c) 2020 Rocky Bernstein


def while1elsestmt(self, lhs, n, rule, ast, tokens, first, last):
    if last == n:
        # Adjust for fuzziness in parsing
        last -= 1

    if tokens[last] == "COME_FROM_LOOP":
        last -= 1
    elif tokens[last - 1] == "COME_FROM_LOOP":
        last -= 2
    if tokens[last] in ("JUMP_BACK", "CONTINUE"):
        # These indicate inside a loop, but token[last]
        # should not be in a loop.
        # FIXME: Not quite right: refine by using target
        return True

    # if SETUP_LOOP target spans the else part, then this is
    # not while1else. Also do for whileTrue?
    last += 1
    # 3.8+ Doesn't have SETUP_LOOP
    return self.version < (3, 8) and tokens[first].attr > tokens[last].off2int()
