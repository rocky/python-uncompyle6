# Test of Python 3's *, or named parameters
# kwargs ::= \e_kwargs kwarg
# kwargs ::= kwargs kwarg
# mkfunc ::= pos_arg \e_kwargs LOAD_CONST LOAD_CONST MAKE_FUNCTION_N2_1
#
def x0(*, file='sample_file'):
    pass

def x1(a, *, file=None):
    pass

def x2(a=5, *, file='filex2'):
    pass

def x3(a=5, *, file='filex2', stuff=None):
    pass
