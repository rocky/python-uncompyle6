#  Copyright (c) 2020-2021 Rocky Bernstein

def except_handler_else(self, lhs, n, rule, ast, tokens, first, last):
    # FIXME: expand this to other versions
    if self.version[:2] not in ((2, 7), (3, 5)):
        return False

    if tokens[first] in ("JUMP_FORWARD", "JUMP_ABSOLUTE"):
        first_jump_target = tokens[first].pattr
        last = min(last, len(tokens)-1)
        for i in range(last, first, -1):
            if tokens[i] == "END_FINALLY":
                i -= 1
                second_jump = tokens[i]
                if second_jump in ("JUMP_FORWARD", "JUMP_ABSOLUTE"):
                    second_jump_target = second_jump.pattr
                    equal_target = second_jump_target == first_jump_target
                    if equal_target:
                        return lhs != "except_handler"
                    else:
                        return lhs != "except_handler_else"
                    pass
                else:
                    return False
            pass
        pass
    return False
