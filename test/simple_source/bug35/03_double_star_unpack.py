# Bug in 3.5 is detecting when there is more than
# one * in a call. There is a "BUILD_UNPACK_LIST" instruction used
# to unpack star arguments
def sum(a, b, c, d):
    return a + b + c + d
a, b, c = 1, 2, 3
args = (1, 2)
sum(*args, *args)

# FIXME: these is handled incorrectly

# sum(a, *args, *args)

# sum(a, b, *args)

# FIXME: this is handled incorrectly
# (*c,) = (3,4)
