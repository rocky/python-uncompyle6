# From Python 3.3.6 hmac.py
# Problem was getting wrong placement of positional args
digest_cons = lambda d=b'': 5

# Handle single kwarg
lambda *, d=0: None
