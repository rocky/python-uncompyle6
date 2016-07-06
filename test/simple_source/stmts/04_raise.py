# 2.6.9 asynccore.py
# Bug in 2.6 was confusing AssertError with an assert statement
# There is special detect code to sort this out based on whether
# we have POP_JUMP_IF_TRUE (2.7) / JUMP_IF_TRUE, POP_TOP

def compact_traceback(tb):
    if not tb: # Must have a traceback
        raise AssertionError("traceback does not exist")
    return
