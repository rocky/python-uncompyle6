# From #227
# Bug was not handling call_ex_kw correctly
# This appears in
#   showparams(c, test="A", **extra_args)
# below

# RUNNABLE!
def showparams(c, test, **extra_args):
    return {'c': c, **extra_args, 'test': test}

def f(c, **extra_args):
    return showparams(c, test="A", **extra_args)

def f1(c, d, **extra_args):
    return showparams(c, test="B", **extra_args)

def f2(**extra_args):
    return showparams(1, test="C", **extra_args)

def f3(c, *args, **extra_args):
    return showparams(c, *args, **extra_args)

assert f(1, a=2, b=3) == {'c': 1, 'a': 2, 'b': 3, 'test': 'A'}

a = {'param1': 2}
assert f1('2', '{\'test\': "4"}', test2='a', **a) \
    == {'c': '2', 'test2': 'a', 'param1': 2, 'test': 'B'}
assert f1(2, '"3"', test2='a', **a) \
    == {'c': 2, 'test2': 'a', 'param1': 2, 'test': 'B'}
assert f1(False, '"3"', test2='a', **a) \
    == {'c': False, 'test2': 'a', 'param1': 2, 'test': 'B'}
assert f(2, test2='A', **a) \
    == {'c': 2, 'test2': 'A', 'param1': 2, 'test': 'A'}
assert f(str(2) + str(1), test2='a', **a) \
    == {'c': '21', 'test2': 'a', 'param1': 2, 'test': 'A'}
assert f1((a.get('a'), a.get('b')), a, test3='A', **a) \
    == {'c': (None, None), 'test3': 'A', 'param1': 2, 'test': 'B'}

b = {'b1': 1, 'b2': 2}
assert f2(**a, **b) == \
    {'c': 1, 'param1': 2, 'b1': 1, 'b2': 2, 'test': 'C'}

c = (2,)
d = (2, 3)
assert f(2, **a) == {'c': 2, 'param1': 2, 'test': 'A'}
assert f3(2, *c, **a) == {'c': 2, 'param1': 2, 'test': 2}
assert f3(*d, **a) == {'c': 2, 'param1': 2, 'test': 3}

# From 3.7 test/test_collections.py
# Bug was in getting **dict(..) right
from collections import namedtuple

Point = namedtuple('Point', 'x y')
p = Point(11, 22)
assert p == Point(**dict(x=11, y=22))

# From 3.7 test/test_keywordonlyarg.py
# Bug was in handling {"4":4} as a dictionary needing **
def posonly_sum(pos_arg1, *arg, **kwarg):
    return pos_arg1 + sum(arg) + sum(kwarg.values())
assert 1+2+3+4 == posonly_sum(1,*(2,3),**{"4":4})

# From 3.7 test_grammar.py
# Bug was in handling keyword-only parameters when there are annotations.
# The stack order from least- to most-recent is:
# default, keyword, annotation, closure
# This changes in between Python 3.5 and 3.6.
def f(a, b: 1, c: 2, d, e: 3=4, f=5, *g: 6, h: 7, i=8, j: 9=10,
      **k: 11) -> 12: pass

assert f.__annotations__ == {'b': 1, 'c': 2, 'e': 3, 'g': 6, 'h': 7, 'j': 9,
                             'k': 11, 'return': 12}
