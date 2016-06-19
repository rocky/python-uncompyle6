# Bug from 3.4 in asyncore.py

def compact_traceback():
    tb = 5
    if not tb: # Must have a traceback
        raise AssertionError("traceback does not exist")
