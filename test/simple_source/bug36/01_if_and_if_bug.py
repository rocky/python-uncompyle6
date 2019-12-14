# Bug in 3.6 was not taking "else" branch after compond "if"
# In earlier versions we had else detection needed here.

# RUNNABLE!
def f(a, b, c):
    if a and b:
        x = 1
    else:
        x = 2
    if c:
        x = 3
    return(x)

assert f(True, True, True) == 3
assert f(True, True, False) == 1
assert f(True, False, True) == 3
assert f(True, False, False) == 2
