# From #227
# Bug was not handling call_ex_kw correctly
# THis appears in
#   showparams(c, test="A", **extra_args)
# below

def showparams(c, test, **extra_args):
    return {'c': c, **extra_args, 'test': test}

def f(c, **extra_args):
    return showparams(c, test="A", **extra_args)

assert f(1, a=2, b=3) == {'c': 1, 'a': 2, 'b': 3, 'test': 'A'}
