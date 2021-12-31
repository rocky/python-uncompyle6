"""This program is self-checking!"""
# Python 2.4 - 2.7 bug in transforming "else if" to "elif" in Python 2.4 .. 2.7
# From Issue #377

# RUNNABLE!
def loop_continue_dead_code(slots):
    for name in slots:
        if name:
            pass
        else:
            continue
            # The below is dead code
            if x:
                y()
            else:
                z()

loop_continue_dead_code([None, 1])
