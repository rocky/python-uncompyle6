a = (1,)
b = (2,3)
a,b = (1,2)
a,b = ( (1,2), (3,4,5) )

x = {}
try:
    x[1,2,3]
except:
    pass

x[1,2,3] = 42
print x[1,2,3]
print x[(1,2,3)]
assert x[(1,2,3)] == x[1,2,3]
del x[1,2,3]

x=[1,2,3]
b=(1 for i in x if i)
b=(e for i in range(4) if i == 2)