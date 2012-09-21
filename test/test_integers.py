import sys
#raise "This program can't be run"

i = 1
i = 42
i = -1
i = -42
i = sys.maxint
minint = -sys.maxint-1
print sys.maxint
print minint
print long(minint)-1

print
i = -2147483647   # == -maxint
print i, repr(i)
i = i-1
print i, repr(i)
i = -2147483648L  # ==  minint   == -maxint-1
print i, repr(i)
i = -2147483649L  # ==  minint-1 == -maxint-2
print i, repr(i)
