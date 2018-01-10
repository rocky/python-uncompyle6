# From python 2.5 make_decorators.py
# Bug was in not recognizing @memoize which uses grammra rules
# using nonterminals mkfuncdeco and mkfuncdeco0
def memoize(func):
    pass
def test_memoize(self):
    @memoize
    def double(x):
        return x * 2
