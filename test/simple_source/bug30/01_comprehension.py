# From abc.py
def __new__(cls, value, bases, namespace):
    {name
     for name, value in namespace.items()
     if getattr(value, "__isabstractmethod__", False)}
    return

# From base64.py
_b32rev = dict([(v[0], k) for k, v in __file__])
