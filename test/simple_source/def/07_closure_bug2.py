# Tests bug in Python 3

# Note also check that *args, and **kwds are preserved
# on the call!

# load_closure ::= LOAD_CLOSURE LOAD_CLOSURE BUILD_TUPLE_2

# Python 3.5
# mkfunc ::= load_closure LOAD_CONST LOAD_CONST MAKE_CLOSURE_0

# Python 3.2
# mkfunc ::= load_closure LOAD_CONST MAKE_CLOSURE_0

# mkfuncdeco0 ::= mkfunc
# mkfuncdeco  ::= expr mkfuncdeco0 CALL_FUNCTION_1
# store       ::= STORE_FAST
# funcdefdeco ::= mkfuncdeco store
# stmt ::= funcdefdeco
from functools import wraps

class ContextDecorator(object):
    def __call__(self, func):
        @wraps(func)
        def inner(*args, **kwds):
            with self._recreate_cm():
                return func(*args, **kwds)
        return inner
