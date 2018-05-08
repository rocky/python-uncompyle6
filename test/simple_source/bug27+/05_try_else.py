# From Python 2.7 test_ziplib.py
# Bug is distinguishing try from try/else.
def testAFakeZlib(self):
    try:
        self.doTest()
    except ImportError:
        if self.compression != 3:
            self.fail("expected test to not raise ImportError")
    else:
        if self.compression != 4:
            self.fail("expected test to raise ImportError")
