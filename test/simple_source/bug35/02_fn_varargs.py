# From python 3.4 pstats.py
# Bug was not adding *, since *args covers that. And getting stream=None
# without *
def __init__(self, *args, stream=None):
    pass
