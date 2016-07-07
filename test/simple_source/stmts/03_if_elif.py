# 2.6.9 symbols.py
# Bug in 2.6 is having multple COME_FROMs due to the
# "and" in the "if" clause
if __name__:
    if __file__ and name:
        pass
    elif name:
        pass
