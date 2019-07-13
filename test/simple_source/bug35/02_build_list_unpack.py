a = 5
x = [1, 2, 3]
i = [(a,), x]
j = [a, *x]

def f1(a):
    return a[0], a[1]

def f2(b):
    return len(b), b[0]+5, b[2]

def f3(x, y):
    return [1, *x, y]

assert f1(i) == ((5,), x)
assert f2(j) == (4, 10, 2)
assert f3(x, a) == [1, 1, 2, 3, 5]
