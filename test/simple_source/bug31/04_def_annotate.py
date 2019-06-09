# Python 3 positional, kwonly, varargs, and annotations. Ick.

# RUNNABLE!
def test1(args_1, c: int, w=4, *varargs: int, **kwargs: 'annotating kwargs') -> tuple:
    return (args_1, c, w, kwargs)

def test2(args_1, args_2, c: int, w=4, *varargs: int, **kwargs: 'annotating kwargs'):
    return (args_1, args_2, c, w, varargs, kwargs)

def test3(c: int, w=4, *varargs: int, **kwargs: 'annotating kwargs') -> float:
    return 5.4

def test4(a: float, c: int, *varargs: int, **kwargs: 'annotating kwargs') -> float:
    return 5.4

def test5(a: float, c: int = 5, *varargs: int, **kwargs: 'annotating kwargs') -> float:
    return 5.4

def test6(a: float, c: int, test=None):
    return (a, c, test)

def test7(*varargs: int, **kwargs):
    return (varargs, kwargs)

def test8(x=55, *varargs: int, **kwargs) -> list:
    return (x, varargs, kwargs)

def test9(arg_1=55, *varargs: int, y=5, **kwargs):
    return x, varargs, int, y, kwargs

def test10(args_1, b: 'annotating b', c: int) -> float:
    return 5.4

class IOBase:
    pass

# Python 3.1 _pyio.py uses the  -> "IOBase" annotation
def o(f, mode = "r", buffering = None) -> "IOBase":
    return (f, mode, buffering)

def foo1(x: 'an argument that defaults to 5' = 5):
    print(x)

def div(a: dict(type=float, help='the dividend'),
        b: dict(type=float, help='the divisor (must be different than 0)')
    ) -> dict(type=float, help='the result of dividing a by b'):
    """Divide a by b"""
    return a / b

class TestSignatureObject1():
    def test_signature_on_wkwonly(self):
        def test(*, a:float, b:str, c:str = 'test', **kwargs: int) -> int:
            pass

class TestSignatureObject2():
    def test_signature_on_wkwonly(self):
        def test(*, c='test', a:float, b:str="S", **kwargs: int) -> int:
            pass

class TestSignatureObject3():
    def test_signature_on_wkwonly(self):
        def test(*, c='test', a:float, kwargs:str="S", **b: int) -> int:
            pass

class TestSignatureObject4():
    def test_signature_on_wkwonly(self):
        def test(x=55, *args, c:str='test', a:float, kwargs:str="S", **b: int) -> int:
            pass

class TestSignatureObject5():
    def test_signature_on_wkwonly(self):
        def test(x=55, *args: int, c='test', a:float, kwargs:str="S", **b: int) -> int:
            pass

class TestSignatureObject5():
    def test_signature_on_wkwonly(self):
        def test(x:int=55, *args: (int, str), c='test', a:float, kwargs:str="S", **b: int) -> int:
            pass

class TestSignatureObject7():
    def test_signature_on_wkwonly(self):
        def test(c='test', kwargs:str="S", **b: int) -> int:
            pass

class TestSignatureObject8():
    def test_signature_on_wkwonly(self):
        def test(**b: int) -> int:
            pass

class TestSignatureObject9():
    def test_signature_on_wkwonly(self):
        def test(a, **b: int) -> int:
            pass

class SupportsInt():

    def __int__(self) -> int:
        pass

def ann1(args_1, b: 'annotating b', c: int, *varargs: str) -> float:
    assert ann1.__annotations__['b'] == 'annotating b'
    assert ann1.__annotations__['c'] == int
    assert ann1.__annotations__['varargs'] == str
    assert ann1.__annotations__['return'] == float

def ann2(args_1, b: int = 5, **kwargs: float) -> float:
    assert ann2.__annotations__['b'] == int
    assert ann2.__annotations__['kwargs'] == float
    assert ann2.__annotations__['return'] == float
    assert b == 5


assert test1(1, 5) == (1, 5, 4, {})
assert test1(1, 5, 6, foo='bar') == (1, 5, 6, {'foo': 'bar'})
assert test2(2, 3, 4) == (2, 3, 4, 4, (), {})
assert test3(10, foo='bar') == 5.4
assert test4(9.5, 7, 6, 4, bar='baz') == 5.4
### FIXME: fill in...
assert test6(1.2, 3) == (1.2, 3, None)
assert test6(2.3, 4, 5) == (2.3, 4, 5)

ann1(1, 'test', 5)
ann2(1)
