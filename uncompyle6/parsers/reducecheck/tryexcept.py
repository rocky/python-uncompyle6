#  Copyright (c) 2020, 2022, 2024 Rocky Bernstein


def tryexcept(self, lhs, n, rule, ast, tokens, first, last):
    come_from_except = ast[-1]
    if rule == (
        "try_except",
        (
            "SETUP_EXCEPT",
            "suite_stmts_opt",
            "POP_BLOCK",
            "except_handler",
            "opt_come_from_except",
        ),
    ):
        if come_from_except[0] == "COME_FROM":
            # There should be at least two COME_FROMs, one from an
            # exception handler and one from the try. Otherwise
            # we have a try/else.
            return True
        pass

    elif rule == (
        "try_except",
        (
            "SETUP_EXCEPT",
            "suite_stmts_opt",
            "POP_BLOCK",
            "except_handler",
            "COME_FROM",
        ),
    ):
        return come_from_except.attr < tokens[first].offset

    elif rule == (
        "try_except",
        (
            "SETUP_EXCEPT",
            "suite_stmts_opt",
            "POP_BLOCK",
            "except_handler",
            "\\e_opt_come_from_except",
        ),
    ):
        # Find END_FINALLY.
        for i in range(last, first, -1):
            if tokens[i] == "END_FINALLY":
                jump_before_finally = tokens[i - 1]
                if jump_before_finally.kind.startswith("JUMP"):
                    if jump_before_finally == "JUMP_FORWARD":
                        # If there is a JUMP_FORWARD before
                        # the END_FINALLY to some jumps place
                        # beyond tokens[last].off2int() then
                        # this is a try/else rather than an
                        # try (no else).
                        return tokens[i - 1].attr > tokens[last].off2int(
                            prefer_last=True
                        )
                    elif jump_before_finally == "JUMP_BACK":
                        # If there is a JUMP_BACK before the
                        # END_FINALLY then this is a looping
                        # jump, but then jumps in the except
                        # handlers have to also be a looping
                        # jump or this is a try/else rather
                        # than an try (no else).
                        except_handler = ast[3]
                        if (
                            except_handler == "except_handler"
                            and except_handler[0] == "JUMP_FORWARD"
                        ):
                            return True
                        return False
                    pass
                pass
            pass
        return False
