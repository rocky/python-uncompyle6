# Tests of Python slice operators

ary = [1,2,3,4,5]
# Forces BUILD_SLICE 2 on 3.x
ary[:2]
ary[2:]
# Forces BUILD_SLICE 3
ary[1:4:2]
