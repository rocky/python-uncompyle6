# Test to see we can a program that has dead code in it.
# This was issue #150
def func(a):
    if a:
        return True
        something_never_run()
