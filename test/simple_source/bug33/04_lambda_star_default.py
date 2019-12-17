# From 3.x test_audiop.py

# Bug is handling default value after * argument in a lambda.
# That's a mouthful of desciption; I am not sure if the really
# hacky fix to the code is even correct.

#
# FIXME: try and test with more than one default argument.

# RUNNABLE
def pack(width, data):
    return (width, data)

packs = {w: (lambda *data, width=w: pack(width, data)) for w in (1, 2, 4)}

assert packs[1]('a') == (1, ('a',))
assert packs[2]('b') == (2, ('b',))
assert packs[4]('c') == (4, ('c',))
