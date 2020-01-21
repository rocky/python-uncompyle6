# Tests:
#
# For Python3:
#   classdef ::= LOAD_BUILD_CLASS mkfunc LOAD_CONST CALL_FUNCTION_2 store
#   mkfunc ::= LOAD_CONST LOAD_CONST MAKE_FUNCTION_0

# For Python2:
#   classdef ::= LOAD_CONST expr mkfunc CALL_FUNCTION_0 BUILD_CLASS store
#   mkfunc ::= LOAD_CONST MAKE_FUNCTION_0

# RUNNABLE!
class A:
    pass

class B(Exception):
    pass

# From 3.x test_descr.py
class MyInt(int):
    class MyInt(int):
        __slots__ = ()
    try:
        (1).__class__ = MyInt
        assert False, "builtin types don't support __class__ assignment."
    except TypeError:
        pass
