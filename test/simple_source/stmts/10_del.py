# Ensures opcodes DELETE_SUBSCR and DELETE_GLOBAL are covered
a = (1, 2, 3)
# DELETE_NAME
del a

# DELETE_SUBSCR
b = [4, 5, 6]
del b[1]
del b[:]

# delete ::= expr expr DELETE_SLICE+1
l = [None] * 10
del l[-2:]

c = [0,1,2,3,4]
del c[:1]
del c[2:3]

d = [0,1,2,3,4,5,6]
del d[1:3:2]

e = ('a', 'b')
def foo():
    # covers DELETE_GLOBAL
    global e
    del e

z = {}

def a():
    b = 1
    global z
    del z
    def b(y):
        global z
        # covers DELETE_FAST
        del y
        # LOAD_DEREF
        return z
