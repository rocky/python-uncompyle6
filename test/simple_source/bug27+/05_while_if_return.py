# Issue #149. Bug in Python 2.7 was handling a return stmt at the end
# of a while with so no jump back, confusing which block the
# return should be part of
def test(a):
    while True:
        if a:
            pass
        else:
            continue
        return
