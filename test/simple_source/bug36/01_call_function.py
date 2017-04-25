# Python 3.6's changes for calling functions.
# See https://github.com/rocky/python-uncompyle6/issues/58
# CALL_FUNCTION_EX takes 2 to 3 arguments on the stack: the function, the tuple of positional arguments,
# and optionally the dict of keyword arguments if bit 0 of oparg is 1.
a(*[])
