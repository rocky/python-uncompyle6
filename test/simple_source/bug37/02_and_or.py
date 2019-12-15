# from 3.7 decompyle3/pytest/validate.py
# 3.7 changes changes "and" to use JUMP_IF_FALSE_OR_POP instead of
# POP_JUMP_IF_FALSE

# RUNNABLE!
def are_instructions_equal(a, b, c, d):
    return a and (b or c) and d

for a, b, c, d, expect in (
        (True, True, False, True, True),
        (True, False, True, True, True),
        (False, False, True, True, False),
        (True, False, True, False, False),
        ):
    assert are_instructions_equal(a, b, c, d) == expect


# FIXME: figure out how to fix properly, and test.
# from 3.7 decompyle3/semantics/pysource.py

# Bug *is* miscompiling to
# if a:
#     if b or c:
#         d = 1
# else:
#     d = 2

def n_alias(a, b, c, d=3):
    if a and b or c:
        d = 1
    else:
        d = 2
    return d

for a, b, c, expect in (
        (True, True, False, 1),
        (True, False, True, 1),
        # (True, False, False, 2), # miscompiles
        # (False, False, True, 1), # miscompiles
        (False, False, False, 2),
        ):
    assert n_alias(a, b, c) == expect, f"{a}, {b}, {c}, {expect}"
