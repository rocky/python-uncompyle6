# Issue #38 in Python 2.7
# Problem is distinguishing 'continue' from 'jump_back'
# in assembly instructions.

# Here, we hack looking for two jump backs
# followed by the end of the except. This
# is a big hack.

for a in [__name__]:
    try:len(a)
    except:continue

# The above has JUMP_ABSOLUTE in it.
#  This has JUMP_FORWARD instead.
for a in [__name__]:
    try:len(a)
    except:continue
    y = 2

# From 2.7.14 decimal.py
# Bug is in handling a CONTINUE op as a result of it being inside
# an except in a loop
def foo(self, error, ordered_errors, vals, funct, Signals):
    for error in ordered_errors:
        try:
            funct(*vals)
        except error:
            pass
        except Signals as e:
            error = e
        else:
            error = 5
