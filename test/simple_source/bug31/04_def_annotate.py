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

class TestSignatureObject(unittest.TestCase):
    def test_signature_on_wkwonly(self):
        def test(*, a:float, b:str) -> int:
            pass

class SupportsInt(_Protocol):

    @abstractmethod
    def __int__(self) -> int:
        pass
