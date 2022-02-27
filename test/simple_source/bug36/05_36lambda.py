# From Python 3.6 hmac.py
# needed to change lambda_body rule
def __init__(self, msg = None, digestmod = None):
    self.digest_cons = lambda d='': digestmod.new(d)

# From Python 3.6 functools.py
# Bug was handling lambda for MAKE_FUNCTION_CLOSURE (closure)
# vs to MAKE_FUNCTION_CLOSURE_POS (pos_args + closure)
def bug():
    def register(cls, func=None):
        return lambda f: register(cls, f)

# From Python 3.6 configparser.py
def items(self, d, section=5, raw=False, vars=None):
    if vars:
        for key, value in vars.items():
            d[self.optionxform(key)] = value
    d = lambda option: self._interpolation.before_get(self,
        section, option, d[option], d)
    return
