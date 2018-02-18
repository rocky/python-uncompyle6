# Bug found in 2.7 test_itertools.py
def test_iziplongest(self):

    # Having a for loop seems important
    for args in ['abc']:
        self.assertEqual(1, 2)

    pass  # Having this seems important

    # The bug was the except jumping back
    # to the beginning of this for loop
    for stmt in [
        "izip_longest('abc', fv=1)",
    ]:
        try:
            eval(stmt)
        except TypeError:
            pass
        else:
            self.fail()
