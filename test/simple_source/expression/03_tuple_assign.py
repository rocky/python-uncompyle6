# Github Issue #57 with Python 2.7
def some_function():
    return ['some_string']

def some_other_function():
    some_variable, = some_function()
    print(some_variable)
