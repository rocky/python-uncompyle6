# Issue 104 seen in Python 3.5
# Since we have empty statement bodies the if's can get confused
# with "and/or". There is a lot of flakiness in control flow here,
# and this needs to be straightened out in a more uniform way
if __file__:
    if __name__:
        pass
    elif __import__:
        pass
