# From python 2.5 make_decorators.py
# Bug was in not recognizing @memoize which uses grammar rules
# using nonterminals mkfuncdeco and mkfuncdeco0

# This file is RUNNABLE!
def memoize(func):
    pass

def test_memoize(self):
    @memoize
    def double(x):
        return x * 2

# Seen in 3.7 test/test_c_locale_coercion.py
# Bug was handling multiple decorators in 3.5+
# simply because we didn't carry over parser rules over from
# earlier versions.

x = 1
def decorator(func):
    def inc_x():
        global x
        x += 1
        func()
    return inc_x

@decorator
@decorator
def fn():
    return

assert x == 1
fn()
assert x == 3
