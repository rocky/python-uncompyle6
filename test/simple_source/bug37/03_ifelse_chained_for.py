# From decompyle3/semantics/customize3.py
# The bug is handling "for" loop inside the
# chained compare ifelse
def n_classdef3(a, b, c, l):
    r = 1
    if 3.0 <= a <= 3.2:
        for n in l:
            if b:
                break
            elif c:
                r = 2
            pass
        pass
    else:
        r = 3
        pass
    return r

assert n_classdef3(10, True, True, []) == 3
assert n_classdef3(0, False, True, []) == 3
assert n_classdef3(3.1, True, True, []) == 1
assert n_classdef3(3.1, True, False, [1]) == 1
assert n_classdef3(3.1, True, True, [2]) == 1
assert n_classdef3(3.1, False, True, [3]) == 2
