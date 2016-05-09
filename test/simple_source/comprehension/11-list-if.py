# Test Python 3.x test semantic handling of
#
#  load_closure ::= LOAD_CLOSURE BUILD_TUPLE_1
#  ...
#  listcomp ::= load_closure LOAD_LISTCOMP LOAD_CONST MAKE_CLOSURE_0 expr GET_ITER CALL_FUNCTION_1

def long_has_args(opt, longopts):
    return [o for o in longopts if o.startswith(opt)]
