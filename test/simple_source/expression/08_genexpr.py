# Bug in Python 3.5.1 calendar.py

# expr ::= LOAD_NAME
# get_iter ::= expr GET_ITER
# expr ::= get_iter
# genexpr ::= LOAD_GENEXPR LOAD_CONST MAKE_FUNCTION_0 expr GET_ITER CALL_FUNCTION_1
# expr ::= genexpr

names = (formatmonthname(False)
             for k in __file__)
