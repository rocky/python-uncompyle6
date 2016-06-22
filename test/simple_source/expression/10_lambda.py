# Bug in Python 3

# Python 3.3+
# mklambda ::= LOAD_LAMBDA LOAD_CONST MAKE_FUNCTION_0
# Python 3.0 .. 3.2
# mklambda ::= LOAD_LAMBDA MAKE_FUNCTION_0

# _mklambda ::= mklambda
# expr ::= _mklambda
# kwarg ::= LOAD_CONST expr
# exprlist ::= exprlist expr
# call_function ::= expr kwarg CALL_FUNCTION_256

import inspect

inspect.formatargvalues(formatvalue=lambda value: __file__)

# bug from python 3.2 calendar
# Handling lambda
months = []
months.insert(0, lambda x: "")

# Python 3.2 configparser.py
class ExtendedInterpolation():
    def items(self, section, option, d):
        value_getter = lambda option: self._interpolation.before_get(self,
            section, option, d[option], d)
        return value_getter
