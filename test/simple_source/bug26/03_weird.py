# From Python 2.6 test_grammar where it says:

# Grammar allows multiple adjacent 'if's in listcomps and genexps,
# even though it's silly. Make sure it works (ifelse broke this.)

[ x for x in range(10) if x % 2 if x % 3 ]
list(x for x in range(10) if x % 2 if x % 3)

# FIXME
# (5 if 1 else max(5, 2))
