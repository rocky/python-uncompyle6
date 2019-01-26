# Bug in Python 2.7 is code creating a (useless) JUMP_ABSOLUTE to the instruction right after
# the "raise" which causes the

# RUNNABLE!
def testit(a, b):
    if a:
        if not b:
            raise AssertionError("test JUMP_ABSOLUTE to next instruction")

def testit2(a, b):
    if a:
        if not b:
            raise AssertionError("test with dead code after raise")
            x = 10

testit(False, True)
testit(False, False)
testit(True, True)

testit2(False, True)
testit2(False, False)
testit2(True, True)
