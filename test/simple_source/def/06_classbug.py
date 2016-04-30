# Python 3.2 Bug from abc.py

# Make sure we handle:

# LOAD_FAST         '__locals__'
# STORE_LOCALS      ''

class abstractclassmethod(object):
    """A Python 3.2 STORE_LOCALS bug
    """

    def __init__(self, callable):
        callable.__isabstractmethod__ = True
