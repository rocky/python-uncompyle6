#  Copyright (c) 2020 Rocky Bernstein

def ifstmt(self, lhs, n, rule, ast, tokens, first, last):
    if lhs == "ifstmtl":
        if last == n:
            last -= 1
            pass
        if tokens[last].attr and isinstance(tokens[last].attr, int):
            return tokens[first].offset < tokens[last].attr
        pass

    # Make sure jumps don't extend beyond the end of the if statement.
    l = last
    if l == n:
        l -= 1
    if isinstance(tokens[l].offset, str):
        last_offset = int(tokens[l].offset.split("_")[0], 10)
    else:
        last_offset = tokens[l].offset
    for i in range(first, l):
        t = tokens[i]
        if t.kind == "POP_JUMP_IF_FALSE":
            pjif_target = t.attr
            if pjif_target > last_offset:
                # In come cases, where we have long bytecode, a
                # "POP_JUMP_IF_FALSE" offset might be too
                # large for the instruction; so instead it
                # jumps to a JUMP_FORWARD. Allow that here.
                if tokens[l] == "JUMP_FORWARD":
                    return tokens[l].attr != pjif_target
                return True
            pass
        pass
    pass

    if ast:
        testexpr = ast[0]

        if (last + 1) < n and tokens[last + 1] == "COME_FROM_LOOP":
            # iflastsmtl jumped outside of loop. No good.
            return True

        if testexpr[0] in ("testtrue", "testfalse"):
            test = testexpr[0]
            if len(test) > 1 and test[1].kind.startswith("jmp_"):
                if last == n:
                    last -= 1
                jmp_target = test[1][0].attr
                if (
                    tokens[first].off2int()
                    <= jmp_target
                    < tokens[last].off2int()
                ):
                    return True
                # jmp_target less than tokens[first] is okay - is to a loop
                # jmp_target equal tokens[last] is also okay: normal non-optimized non-loop jump
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
        pass
    return False
