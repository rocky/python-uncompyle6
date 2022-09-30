#  Copyright (c) 2020, 2022 Rocky Bernstein
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or



def and_invalid( self, lhs, n, rule, ast, tokens, first, last):
    jmp = ast[1]
    if jmp.kind.startswith("jmp_"):
        if last == n:
            return True
        jmp_target = jmp[0].attr
        jmp_offset = jmp[0].offset

        if tokens[first].off2int() <= jmp_target < tokens[last].off2int():
            return True
        if rule == ("and", ("expr", "jmp_false", "expr", "jmp_false")):
            jmp2_target = ast[3][0].attr
            return jmp_target != jmp2_target
        elif rule == ("and", ("expr", "jmp_false", "expr", "POP_JUMP_IF_TRUE")):
            jmp2_target = ast[3].attr
            return jmp_target == jmp2_target
        elif rule == ("and", ("expr", "jmp_false", "expr")):
            if tokens[last] == "POP_JUMP_IF_FALSE":
                # Ok if jump_target doesn't jump to last instruction
                return jmp_target != tokens[last].attr
            elif tokens[last] in ("POP_JUMP_IF_TRUE", "JUMP_IF_TRUE_OR_POP"):
                # Ok if jump_target jumps to a COME_FROM after
                # the last instruction or jumps right after last instruction
                if last + 1 < n and tokens[last + 1] == "COME_FROM":
                    return jmp_target != tokens[last + 1].off2int()
                return jmp_target + 2 != tokens[last].attr
        elif rule == ("and", ("expr", "jmp_false", "expr", "COME_FROM")):
            return ast[-1].attr != jmp_offset
        # elif rule == ("and", ("expr", "jmp_false", "expr", "COME_FROM")):
        #     return jmp_offset != tokens[first+3].attr

        return jmp_target != tokens[last].off2int()
    return False
