# Tests in Python 3:
#
# load_genexpr ::= BUILD_TUPLE_1 LOAD_GENEXPR LOAD_CONST
# genexpr ::= load_closure load_genexpr MAKE_CLOSURE_0 expr GET_ITER CALL_FUNCTION_1

def __instancecheck__(cls, instance):
    return any(cls.__subclasscheck__(c) for c in {subclass, subtype})
