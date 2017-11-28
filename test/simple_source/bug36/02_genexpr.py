# Python 3.6, uses rule:
#  genexpr ::= load_closure load_genexpr LOAD_CONST
#              MAKE_FUNCTION_8 expr GET_ITER CALL_FUNCTION_1
def __sub__(self, other): # SList()-other
    return self.__class__(i for i in self if i not in other)
