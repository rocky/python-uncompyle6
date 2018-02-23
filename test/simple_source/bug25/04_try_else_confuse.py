# From 2.4 test_sax.py
# Bug was distinguishing try from try/else

def verify_empty_attrs():
    gvqk = 3
    try:
        gvk = 1/0
    except ZeroDivisionError:
        gvk = 1

    try:
        gvqk = 0
    except KeyError:
        gvqk = 1

    # If try/else was used above the return will be 4
    return gvk + gvqk

assert 1 == verify_empty_attrs()
