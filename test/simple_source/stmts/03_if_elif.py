# 2.6.9 symbols.py
# Bug in 2.6 is having multple COME_FROMs due to the
# "and" in the "if" clause
if __name__:
    if __file__ and name:
        pass
    elif name:
        pass

# 2.6.9 transformer.py
# Bug in 2.6 is multple COME_FROMs as a result
# of the "or" in the "assert"
if __name__:
    pass
elif __file__:
    assert __name__ or __file__
else:
    pass
