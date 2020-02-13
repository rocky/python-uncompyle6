# 2.6.9 symbols.py
# Bug in 2.6 is having multple COME_FROMs due to the
# "and" in the "if" clause

# RUNNABLE
if __name__:
    if __file__ and __name__:
        pass
    elif not __name__:
        assert False

# 2.6.9 transformer.py
# Bug in 2.6 is multple COME_FROMs as a result
# of the "or" in the "assert"

# In PyPy the assert is handled via PyPy's unique JUMP_IF_NOT_DEBUG
# instruction.

# Also note that the "else: pass" is superfluous
if __name__:
    pass
elif __file__:
    assert __name__ or __file__
else:
    pass

# From 3.3.7 test_binop.py
# Bug was in ifelsestmt(c) ensuring b+=5 is not in "else"
# Also note: ifelsetmtc should not have been used since this
# this is not in a loop!
def __floordiv__(a, b):
    if a:
        b += 1
    elif not b:
        return a
    b += 5
    return b

assert __floordiv__(1, 1) == 7
assert __floordiv__(1, 0) == 6
assert __floordiv__(0, 3) == 8
assert __floordiv__(0, 0) == 0
