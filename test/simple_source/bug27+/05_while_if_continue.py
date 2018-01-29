# Issue 151 for Python 2.7
# Bug was two-fold. Not having a rile for a while loop with an ending return statement
# and allowing iflastsmtl to have an optional c_stmt which allowed the "if" to get
# comined into the "while". A separate analysis for control flow should make this
# simpiler.
def func(a, b, c):
    while a:
        if b:
            continue
        return False
    return True
