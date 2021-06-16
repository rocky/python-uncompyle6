# From https://github.com/rocky/python-uncompyle6/issues/350
# This is RUNNABLE!
a = (lambda x: x)(abs)
assert a(-3) == 3
