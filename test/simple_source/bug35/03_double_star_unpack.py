# Bug in Python 3.5 is getting the two star'd arguments right.
def sum(a,b,c,d):
    return a + b + c + d

args=(1,2)
sum(*args, *args)

# FIXME: this is handled incorrectly
# (*c,) = (3,4)
