# Issue #284 in Python 2.6
# See https://github.com/rocky/python-uncompyle6/issues/284
# Decompilation failed when return was the last statetement
# in the while loop inside the if block

# This code is RUNNABLE!

def f1():
    if True:
        while True:
            return 5

def f2():
    if True:
        while 1:
            return 6


assert f1() == 5 and f2() == 6
