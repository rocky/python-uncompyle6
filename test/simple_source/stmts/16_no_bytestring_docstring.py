"""Module docstring"""
class A:
    b"""Got \xe7\xfe Bytes?"""
    assert __doc__ == """Module docstring"""

    def class_func(self):
       b"""Got \xe7\xfe Bytes?"""
       assert __doc__ == """Module docstring"""

class B:
    """Got no Bytes?"""
    assert __doc__ == """Got no Bytes?"""

    def class_func(self):
        """Got no Bytes?"""
        assert __doc__ == """Module docstring"""

def single_func():
    """single docstring?"""
    assert __doc__ == """Module docstring"""

def single_byte_func():
    b"""Got \xe7\xfe Bytes?"""
    assert __doc__ == """Module docstring"""

assert __doc__ == """Module docstring"""

assert single_func.__doc__ == """single docstring?"""
single_func()

assert single_byte_func.__doc__ is None
single_byte_func()

assert A.__doc__ is None
assert A.class_func.__doc__ is None
a = A()
assert a.class_func.__doc__ is None
a.class_func()

assert B.__doc__ == """Got no Bytes?"""
assert B.class_func.__doc__ == """Got no Bytes?"""
b = B()
assert b.class_func.__doc__ == """Got no Bytes?"""
b.class_func()

