#  Copyright (c) 2020 Rocky Bernstein


def iflaststmt(self, lhs, n, rule, ast, tokens, first, last):
    testexpr = ast[0]

    if testexpr[0] in ("testtrue", "testfalse"):

        test = testexpr[0]
        if len(test) > 1 and test[1].kind.startswith("jmp_"):
            if last == n:
                last -= 1
            jmp_target = test[1][0].attr
            if tokens[first].off2int() <= jmp_target < tokens[last].off2int():
                return True
            # jmp_target less than tokens[first] is okay - is to a loop
            # jmp_target equal tokens[last] is also okay: normal non-optimized non-loop jump

            if (
                (last + 1) < n
                and tokens[last - 1] != "JUMP_BACK"
                and tokens[last + 1] == "COME_FROM_LOOP"
            ):
                # iflastsmtl is not at the end of a loop, but jumped outside of loop. No good.
                # FIXME: check that tokens[last] == "POP_BLOCK"? Or allow for it not to appear?
                return True

            # If the instruction before "first" is a "POP_JUMP_IF_FALSE" which goes
            # to the same target as jmp_target, then this not nested "if .. if .."
            # but rather "if ... and ..."
            if first > 0 and tokens[first - 1] == "POP_JUMP_IF_FALSE":
                return tokens[first - 1].attr == jmp_target

            if jmp_target > tokens[last].off2int():
                # One more weird case to look out for
                #   if c1:
                #      if c2:  # Jumps around the *outer* "else"
                #       ...
                #   else:
                if jmp_target == tokens[last - 1].attr:
                    return False
                if last < n and tokens[last].kind.startswith("JUMP"):
                    return False
                return True

        pass
    return False
