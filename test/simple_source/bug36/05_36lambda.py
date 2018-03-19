# From Python 3.6 hmac.py
# needed to change mklamba rule
def __init__(self, msg = None, digestmod = None):
    self.digest_cons = lambda d='': digestmod.new(d)
