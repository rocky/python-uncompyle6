# From 2.4 test_binop.py bug is missing 'else:' in 2nd try.
def test_constructor():
    for bad in "0", 0.0, 0j, (), [], {}, None:
        try:
            raise TypeError(bad)
        except TypeError:
            pass
        else:
            assert False, "%r didn't raise TypeError" % bad
        try:
            raise TypeError(bad)
        except TypeError:
            pass
        else:
            assert False, "%r didn't raise TypeError" % bad

test_constructor()
