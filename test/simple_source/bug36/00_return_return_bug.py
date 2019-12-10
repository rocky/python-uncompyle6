# Bug in 3.6 and above.
#Not detecting 2nd return is outside of
# if/then. Fix was to ensure COME_FROM

# RUNNABLE!
def return_return_bug(foo):
    if foo == 'say_hello':
        return "hello"
    return "world"

assert return_return_bug('say_hello') == 'hello'
assert return_return_bug('world') == 'world'
