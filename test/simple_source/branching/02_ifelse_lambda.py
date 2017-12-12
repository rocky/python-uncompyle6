# We have to do contortions here because
# lambda's have to be more or less on a line

f = lambda x: 1 if x<2 else 3
f(5)

# If that wasn't enough ...
# Python will create dead code
# in the below. So we must make sure
# not to include the else expression

g = lambda: 1 if True else 3
g()

h = lambda: 1 if False else 3
h()

# From 2.7 test_builtin
lambda c: 'a' <= c <= 'z', 'Hello World'
