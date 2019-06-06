# Python 3 annotations

def foo(a, b: 'annotating b', c: int) -> float:
    print(a + b + c)

# Python 3.1 _pyio.py uses the  -> "IOBase" annotation
def open(file, mode = "r", buffering = None,
         encoding = None, errors = None,
         newline = None, closefd = True) -> "IOBase":
    return text

def foo1(x: 'an argument that defaults to 5' = 5):
    print(x)

def div(a: dict(type=float, help='the dividend'),
        b: dict(type=float, help='the divisor (must be different than 0)')
    ) -> dict(type=float, help='the result of dividing a by b'):
    """Divide a by b"""
    return a / b

class TestSignatureObject():
    def test_signature_on_wkwonly(self):
        def test(*, a:float, b:str) -> int:
            pass

class SupportsInt():

    def __int__(self) -> int:
        pass

def foo2(a, b: 'annotating b', c: int, *args: str) -> float:
    assert foo2.__annotations__['b'] == 'annotating b'
    assert foo2.__annotations__['c'] == int
    assert foo2.__annotations__['args'] == str
    assert foo2.__annotations__['return'] == float

def foo3(a, b: int = 5, **kwargs: float) -> float:
    assert foo3.__annotations__['b'] == int
    assert foo3.__annotations__['kwargs'] == float
    assert foo3.__annotations__['return'] == float
    assert b == 5



foo2(1, 'test', 5)
foo3(1)
