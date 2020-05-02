# Python 3.3+
#
# From Python 3.3.6 hmac.py
# Problem was getting wrong placement of positional args.
# In 3.6+ parameter handling changes

# RUNNABLE!

digest_cons = lambda d=b'': 5

# Handle single kwarg
x = lambda *, d=0: d
assert x(d=1) == 1
assert x() == 0
