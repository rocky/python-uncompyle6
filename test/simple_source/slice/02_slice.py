# Self-checking test.
# Tests of Python slice operators

ary = [1,2,3,4,5]

# Forces BUILD_SLICE 2 on 3.x
a = ary[:2]
assert a == [1, 2]

a = ary[2:]
assert a == [3, 4, 5]

# Forces BUILD_SLICE 3
a = ary[1:4:2]
assert a == [2, 4]
