# 2.6.9 symbols.py
# Bug in 2.6 is having multple COME_FROMs due to the
# "and" in the "if" clause
if __name__:
    if __file__ and __name__:
        pass
    elif __name__:
        pass

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
