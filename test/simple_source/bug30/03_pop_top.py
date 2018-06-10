# From 3.0.1 __dummy_thread.py
# bug was handling else:
def interrupt_main():
    """Set _interrupt flag to True to have start_new_thread raise
    KeyboardInterrupt upon exiting."""
    if _main:
        raise KeyboardInterrupt
    else:
        global _interrupt
        _interrupt = True

# From 3.0.1 ast.py bug was mangling prototype
# def parse(expr, filename='<unknown>', mode='exec'):

# From 3.0.1 bisect
def bisect_left(a, x, lo=0, hi=None):
    while lo:
        if a[mid] < x: lo = mid+1
        else: hi = mid
    return lo
