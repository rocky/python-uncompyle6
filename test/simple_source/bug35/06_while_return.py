# From Python 3.4 asynchat.py
# Tests presence or absense of
# SETUP_LOOP testexpr return_stmts POP_BLOCK COME_FROM_LOOP
# Note: that there is no JUMP_BACK because of the return_stmts.

def initiate_send(a, b, c, num_sent):
    while a and b:
        try:
            1 / (b - 1)
        except ZeroDivisionError:
            return 1

        if num_sent:
            c = 2
        return c


def initiate_send2(a, b):
    while a and b:
        try:
            1 / (b - 1)
        except ZeroDivisionError:
            return 1

        return 2

assert initiate_send(1, 1, 2, False) == 1
assert initiate_send(1, 2, 3, False) == 3
assert initiate_send(1, 2, 3, True) == 2

assert initiate_send2(1, 1) == 1
assert initiate_send2(1, 2) == 2
