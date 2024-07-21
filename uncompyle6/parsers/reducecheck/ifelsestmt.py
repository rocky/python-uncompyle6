#  Copyright (c) 2020-2022 Rocky Bernstein

from uncompyle6.scanners.tok import Token

IFELSE_STMT_RULES = frozenset(
    [
        (
            "ifelsestmt",
            (
                "testexpr",
                "c_stmts_opt",
                "jump_forward_else",
                "else_suite",
                "_come_froms",
            ),
        ),
        (
            "ifelsestmt",
            (
                "testexpr",
                "c_stmts_opt",
                "jump_forward_else",
                "else_suite",
                "\\e__come_froms",
            ),
        ),
        (
            "ifelsestmtl",
            (
                "testexpr",
                "c_stmts_opt",
                "jump_forward_else",
                "else_suitec",
            ),
        ),
        (
            "ifelsestmtc",
            (
                "testexpr",
                "c_stmts_opt",
                "jump_forward_else",
                "else_suitec",
                "\\e__come_froms",
            ),
        ),
        (
            "ifelsestmtc",
            (
                "testexpr",
                "c_stmts_opt",
                "jump_absolute_else",
                "else_suitec",
            ),
        ),
        (
            "ifelsestmtc",
            (
                "testexpr",
                "c_stmts_opt",
                "JUMP_ABSOLUTE",
                "else_suitec",
            ),
        ),
        (
            "ifelsestmt",
            (
                "testexpr",
                "c_stmts_opt",
                "jf_cfs",
                "else_suite",
                "\\e_opt_come_from_except",
            ),
        ),
        (
            "ifelsestmt",
            (
                "testexpr",
                "c_stmts_opt",
                "JUMP_FORWARD",
                "else_suite",
                "come_froms",
            ),
        ),
        (
            "ifelsestmtc",
            ("testexpr", "c_stmts_opt", "JUMP_FORWARD", "else_suite", "come_froms"),
        ),
        (
            "ifelsestmt",
            (
                "testexpr",
                "c_stmts",
                "come_froms",
                "else_suite",
                "come_froms",
            ),
        ),
        (
            "ifelsestmt",
            (
                "testexpr",
                "c_stmts_opt",
                "jf_cfs",
                "else_suite",
                "opt_come_from_except",
            ),
        ),
        (
            "ifelsestmt",
            (
                "testexpr",
                "c_stmts_opt",
                "jf_cf_pop",
                "else_suite",
            ),
        ),
        (
            "ifelsestmt",
            (
                "testexpr",
                "stmts",
                "jf_cfs",
                "else_suite_opt",
                "opt_come_from_except",
            ),
        ),
        (
            "ifelsestmt",
            (
                "testexpr",
                "stmts",
                "jf_cfs",
                "\\e_else_suite_opt",
                "\\e_opt_come_from_except",
            ),
        ),
        (
            "ifelsestmt",
            (
                "testexpr",
                "stmts",
                "jf_cfs",
                "\\e_else_suite_opt",
                "opt_come_from_except",
            ),
        ),
    ]
)


def ifelsestmt(self, lhs, n, rule, tree, tokens, first, last):
    if (last + 1) < n and tokens[last + 1] == "COME_FROM_LOOP" and lhs != "ifelsestmtc":
        # ifelsestmt jumped outside of loop. No good.
        return True

    # print("XXX", first, last)
    # for t in range(first, last):
    #     print(tokens[t])
    # print("=" * 30)

    first_offset = tokens[first].off2int()

    if rule not in IFELSE_STMT_RULES:
        # print("XXX", rule)
        return False

    # Avoid if/else where the "then" is a "raise_stmt1" for an
    # assert statement. Parse this as an "assert" instead.
    stmts = tree[1]
    if stmts in ("c_stmts",) and len(stmts) == 1:
        raise_stmt1 = stmts[0]
        if raise_stmt1 == "raise_stmt1" and raise_stmt1[0] in ("LOAD_ASSERT",):
            return True

    # Make sure all the offsets from the "COME_FROMs" at the
    # end of the "if" come from somewhere inside the "if".
    # Since the come_froms are ordered so that lowest
    # offset COME_FROM is last, it is sufficient to test
    # just the last one.
    if len(tree) == 5:
        end_come_froms = tree[-1]
        if end_come_froms.kind != "else_suite" and self.version >= (3, 0):
            if end_come_froms == "opt_come_from_except" and len(end_come_froms) > 0:
                end_come_froms = end_come_froms[0]
            if not isinstance(end_come_froms, Token):
                if len(end_come_froms):
                    return first_offset > end_come_froms[-1].attr
            elif first_offset > end_come_froms.attr:
                return True

        # FIXME: There is weirdness in the grammar we need to work around.
        # we need to clean up the grammar.
        if self.version < (3, 0):
            last_token = tree[-1]
        else:
            last_token = tokens[last]
        if last_token == "COME_FROM" and first_offset > last_token.attr:
            if (
                self.version < (3, 0)
                and self.insts[self.offset2inst_index[last_token.attr]].opname
                != "SETUP_LOOP"
            ):
                return True

    testexpr = tree[0]

    # Check that the condition portion of the "if"
    # jumps to the "else" part.
    if testexpr[0] in ("testtrue", "testfalse"):
        if_condition = testexpr[0]

        else_suite = tree[3]
        assert else_suite.kind.startswith("else_suite")

        if len(if_condition) > 1 and if_condition[1].kind.startswith("jmp_"):
            if last == n:
                last -= 1
            jmp = if_condition[1]
            if self.version >= (2, 7):
                jmp_target = jmp[0].attr
            else:
                jmp_target = int(jmp[0].pattr)

            # Below we check that jmp_target is jumping to a feasible
            # location. It should be to the transition after the "then"
            # block and to the beginning of the "else" block.
            # However the "if/else" is inside a loop the false test can be
            # back to the loop.

            # FIXME: the below logic for jf_cfs could probably be
            # simplified.
            jump_else_end = tree[2]
            if jump_else_end == "jf_cf_pop":
                jump_else_end = jump_else_end[0]

            if jump_else_end == "JUMP_FORWARD":
                endif_target = int(jump_else_end.pattr)
                last_offset = tokens[last].off2int()
                if endif_target != last_offset:
                    return True
            last_offset = tokens[last].off2int(prefer_last=False)
            if jmp_target == last_offset:
                # jmp_target should be jumping to the end of the if/then/else
                # but is it jumping to the beginning of the "else"
                return True
            if (
                jump_else_end in ("jf_cfs", "jump_forward_else")
                and jump_else_end[0] == "JUMP_FORWARD"
            ):
                # If the "else" jump jumps before the end of the the "if .. else end", then this
                # is not this kind of "ifelsestmt".
                jump_else_forward = jump_else_end[0]
                jump_else_forward_target = jump_else_forward.attr
                if jump_else_forward_target < last_offset:
                    return True
                pass
            if (
                jump_else_end in ("jb_elsec", "jb_elsel", "jf_cfs", "jb_cfs")
                and jump_else_end[-1] == "COME_FROM"
            ):
                if jump_else_end[-1].off2int() != jmp_target:
                    return True

            if first_offset > jmp_target:
                # A backward or loop jump from the end of an "else"
                # clause before the beginning of the "if" test is okay
                # only if we are trying to match or reduce an "if"
                # statement of the kind that can occur only inside a
                # loop construct.

                if lhs in ("ifelsestmtl", "ifelsestmtc"):
                    jump_false = jmp
                    if (
                        tree[2].kind in ("JUMP_FORWARD", "JUMP_ABSOLUTE")
                        and jump_false == "jmp_false"
                        and len(else_suite) == 1
                    ):
                        suite_stmts = else_suite[0]
                        continue_stmt = suite_stmts[0]
                        if (
                            suite_stmts in ("suite_stmts", "c_stmts")
                            and len(suite_stmts) == 1
                            and continue_stmt == "continue"
                            and jump_false[0].attr == continue_stmt[0].attr
                        ):
                            # for ...:
                            #   if ...:
                            #     ...
                            #   else:
                            #     continue
                            return False
                return True

            return (jmp_target > last_offset) and tokens[last] != "JUMP_FORWARD"

    return False
