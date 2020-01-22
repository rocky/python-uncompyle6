# In Python 3.2 JUMP_ABSOLUTE's (which can
# turn into COME_FROM's) are not optimized as
# they are in later Python's.
#
# So an if statement can jump to the end of a for loop
# which in turn jump's back to the beginning of that loop.
#
# Should handle in Python 3.2
#
#          98	JUMP_BACK         '16' statement after: names.append(name) to loop head
#       101_0	COME_FROM         '50' statement: if name == ...to fictional "end if"
#         101	JUMP_BACK         '16' jump as before to loop head

# RUNNABLE!
def _slotnames(cls):
    names = []
    for c in cls.__mro__:
        if "__slots__" in c.__dict__:
            slots = c.__dict__['__slots__']
            for name in slots:
                if name == "__dict__":
                    continue
                else:
                    names.append(name) # 3.2 bug here jumping to outer for

# From 3.2.6 pdb.py
# There is no "come_from" after the "if" since the
# if jumps back to the loop. For this we use
# grammar rule "ifstmtl"
def lasti2lineno(linestarts, a):
    for i in linestarts:
        if a:
            return a
    return -1

assert lasti2lineno([], True) == -1
assert lasti2lineno([], False) == -1
assert lasti2lineno([1], False) == -1
assert lasti2lineno([1], True) == 1

# From 3.7 test_builtin.py
# Bug was allowing if condition jump back to the
# "for" loop as an acceptable "ifstmtl" rule.

# RUNNABLE!
def test_pow(m, b, c):
    for a in m:
        if a or \
           b or \
           c:
            c = 1

    return c

assert test_pow([], 2, 3) == 3
assert test_pow([1], 0, 5) == 1
assert test_pow([1], 4, 2) == 1
assert test_pow([0], 0, 0) == 0
