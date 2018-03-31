# From 3.6.4 configparser.py
# Bug in 3.6 was handling "else" with compound
# if. there is no POP_BLOCK and
# there are several COME_FROMs before the else
def _read(self, fp, a, value, f):
    for line in fp:
        for prefix in a:
            fp()
        if (value and fp and
            prefix > 5):
            f()
        else:
            f()
