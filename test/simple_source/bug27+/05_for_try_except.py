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
