#  Copyright (c) 2020 Rocky Bernstein

from uncompyle6.parsers.treenode import SyntaxTree

def tryelsestmtl3(self, lhs, n, rule, ast, tokens, first, last):
    # Check the end of the except handler that there isn't a jump from
    # inside the except handler to the end. If that happens
    # then this is a "try" with no "else".
    except_handler = ast[3]

    if except_handler == "except_handler_else":
        except_handler = except_handler[0]

    come_from = except_handler[-1]
    # We only care about the *first* come_from because that is the
    # the innermost one. So if the "tryelse" is invalid (should be a "try")
    # it will be invalid here.
    if come_from == "COME_FROM":
        first_come_from = except_handler[-1]
    elif come_from == "END_FINALLY":
        return False
    elif come_from == "except_return":
        return False
    else:
        assert come_from in ("come_froms", "opt_come_from_except")
        first_come_from = come_from[0]
        if not hasattr(first_come_from, "attr"):
            # optional come from
            return False

    leading_jump = except_handler[0]
    if not hasattr(leading_jump, "offset"):
        return False

    # We really don't care that this is a jump per-se. But
    # we could also check that this jumps to the end of the except if
    # desired.
    if isinstance(leading_jump, SyntaxTree):
        except_handler_first_offset = leading_jump.first_child().off2int()
    else:
        except_handler_first_offset = leading_jump.off2int()

    return first_come_from.attr > except_handler_first_offset
