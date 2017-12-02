# Tests closure bug in Python 3

# Note also check that *args, and **kwds are preserved
# on the call!

# load_closure ::= LOAD_CLOSURE BUILD_TUPLE_1

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

def contextmanager(func):
    @wraps(func)
    def helper(*args, **kwds):
        return _GeneratorContextManager(func, *args, **kwds)
    return helper
