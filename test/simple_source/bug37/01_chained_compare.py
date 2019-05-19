# From Python 3.7 pickle.py
# Bug was different code generation for chained comparisons than prior Python versions


def chained_compare_a(protocol):
    if not 0 <= protocol <= 7:
        raise ValueError("pickle protocol must be <= %d" % 7)

def chained_compare_b(a, obj):
    if a:
        if -0x80000000 <= obj <= 0x7fffffff:
            return 5

def chained_compare_c(a, d):
    for i in len(d):
        if a == d[i] != 2:
            return 5

chained_compare_a(3)
try:
    chained_compare_a(8)
except ValueError:
    pass
chained_compare_b(True, 0x0)

chained_compare_c(3, [3])
