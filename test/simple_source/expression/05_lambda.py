# Bug in Python 3

# mklambda ::= LOAD_LAMBDA LOAD_CONST MAKE_FUNCTION_0
# _mklambda ::= mklambda
# expr ::= _mklambda
# kwarg ::= LOAD_CONST expr
# exprlist ::= exprlist expr
# call_function ::= expr kwarg CALL_FUNCTION_256

inspect.formatargvalues(formatvalue=lambda value: __file__)
