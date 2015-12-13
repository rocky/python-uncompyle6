i = 1; j = 7
def a():
    def b():
        def c():
            k = 34
            global i
            i = i+k
        l = 42
        c()
        global j
        j = j+l
    b()
    print i, j # should print 35, 49

a()
print i, j
