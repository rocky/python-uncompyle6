# Self-checking test.
# Bug was in if transform not inverting expression
# This file is RUNNABLE!
def test_assert2(c):
    if c < 2:
        raise SyntaxError('Oops')

test_assert2(5)
