def x0():
    pass

def x1(a):
    pass


def x2(a=5):
    pass

def x3(a, b, c=5):
    pass

def x4(a, b=5, **c):
    pass

# Had a bug in 2.x where
# we weren't picking up **kwds when
# it was the sole parameter
def funcattrs(**kwds):
    return
