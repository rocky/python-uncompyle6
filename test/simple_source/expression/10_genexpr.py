# From Python 3.4 calendar

# load_closure ::= LOAD_CLOSURE
# load_closure ::= load_closure LOAD_CLOSURE
# expr ::= LOAD_GLOBAL
# get_iter ::= expr GET_ITER
# genexpr ::= load_closure LOAD_GENEXPR LOAD_CONST MAKE_CLOSURE_0 expr GET_ITER CALL_FUNCTION_
def formatyear(self, theyear, m=3):
    for (i, row) in enumerate(self.yeardays2calendar(theyear, m)):
        names = (self.formatmonthname(theyear, k, colwidth, False)
                 for k in months)
