# Bug in 3.5 is detecting when there is more than
# one * in a call. There is a "BUILD_UNPACK_LIST" instruction used
# to unpack star arguments
def sum(a, b, c, d):
    return a + b + c + d

args, a, b, c = (1, 2), 1, 2, 3
sum(*args, *args)
sum(*args, *args, *args)

sum(a, *args, *args)
sum(a, b, *args)
sum(a, b, *args, *args)

# FIXME: this is handled incorrectly
# (*c,) = (3,4)
