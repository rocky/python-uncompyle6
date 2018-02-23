# From 2.4 test_array.py
# In Python 2.4 and earlier "yield" is not valid and instead
# we must use "yield None". Bug was not adding "None"

def yield_bug():
    yield None
    return
