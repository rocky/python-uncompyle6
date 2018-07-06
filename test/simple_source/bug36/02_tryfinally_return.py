# Python 3.6 sometimes omits END_FINALLY. See issue #182
def foo():
    try:
        x = 1
    finally:
        return
