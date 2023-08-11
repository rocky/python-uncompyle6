# RUNNABLE!
# From issue 469

"""This program is self-checking!"""

my_dict = (lambda variable0: {variable1: 123 for variable1 in variable0})([1, 2, 3])

assert my_dict[1] == 123

my_set = (lambda variable0: {variable1 for variable1 in variable0})([1, 2, 3])
assert 2 in my_set
