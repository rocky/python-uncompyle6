# From 3.2 _abcoll.py
def pop(self):
    it = iter(self)
    try:
        value = next(it)
    except StopIteration:
        raise KeyError
    self.discard(value)
    return value
