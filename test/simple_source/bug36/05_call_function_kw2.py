# From 3.6 _pydecimal. Bug was handling
# keyword args in the return (CALL_FUNCTION_KW_2)
def to_eng_string(self, context=None):
    return self.__str__(eng=True, context=context)
