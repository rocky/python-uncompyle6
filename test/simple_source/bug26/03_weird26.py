# From Python 2.6 test_grammar where it says:

# Grammar allows multiple adjacent 'if's in listcomps and genexps,
# even though it's silly. Make sure it works (ifelse broke this.)

[ x for x in range(10) if x % 2 if x % 3 ]
list(x for x in range(10) if x % 2 if x % 3)

# expresion which evaluates True unconditionally,
# but leave dead code or junk around that we have to match on.
# Tests "if_exp_true" rule
5 if 1 else 2

0 or max(5, 3) if 0 else 3
