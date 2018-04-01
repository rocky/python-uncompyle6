# From 3.6.4 pathlib.py
# Bug was handling "continue" as last statement of "if"
# RUNNABLE!
def parse_parts(it, parts):
    for part in it:
        if not part:
            continue
        parts = 1
    return parts

assert parse_parts([], 5) == 5
assert parse_parts([True], 6) == 1
assert parse_parts([False], 6) == 6
