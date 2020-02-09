# We have to do contortions here because
# lambda's have to be more or less on a line

f = lambda x: 1 if x < 2 else 3
assert f(3) == 3
assert f(1) == 1

# If that wasn't enough ...
# Python will create dead code
# in the below. So we must make sure
# not to include the else expression

g = lambda: 1 if True else 3
assert g() == 1

h = lambda: 1 if False else 3
assert h() == 3

# From 2.7 test_builtin
i = lambda c: 'a' <= c <= 'z', 'Hello World'
assert i[0]('a') == True
assert i[0]('A') == False

# Issue #170. Bug is needing an "conditional_not_lambda" grammar rule
# in addition the the "if_exp_lambda" rule
j = lambda a: False if not a else True
assert j(True) == True
assert j(False) == False
