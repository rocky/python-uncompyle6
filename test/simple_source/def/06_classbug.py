# Python 3.2 Bug from abc.py

# Make sure we handle:

# LOAD_FAST         '__locals__'
# STORE_LOCALS      ''

# Note this is similar to 05_abc_class.py but not the same:
#  object -> classmethod

class abstractclassmethod(object):
    """A Python 3.2 STORE_LOCALS bug
    """

    def __init__(self, callable):
        callable.__isabstractmethod__ = True
