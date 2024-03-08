"""
This program is self checking!
"""


class TestContextManager:
    def __enter__(self):
        return 1, 2

    def __exit__(self, exc_type, exc_value, exc_tb):
        return self, exc_type, exc_value, exc_tb


with open(__file__) as a:
    assert a

with open(__file__) as a, open(__file__) as b:
    assert a.read() == b.read()

with TestContextManager() as a, b:
    assert (a, b) == (1, 2)
