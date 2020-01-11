# Self-checking test.
# Bug was in if transform not inverting expression
# This file is RUNNABLE!
def test_assert2(c):
    if c < 2:
        raise SyntaxError('Oops')

test_assert2(5)

# Bug is handling "assert" and confusing it with "or".
# It is important that the assert be at the end of the loop.
for x in (2, 4, 6):
    assert x == x

# Bug in 3.7 was not having a rule for 2-arg assert.
# 2-arg assert code doesn't match "if not ... raise "
for x in (1, 3, 5):
    assert x == x, "foo"
