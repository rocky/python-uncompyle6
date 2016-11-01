# Python 3 annotations

def foo(a, b: 'annotating b', c: int) -> float:
    print(a + b + c)

# Python 3.1 _pyio.py uses the  -> "IOBase" annotation
def open(file, mode = "r", buffering = None,
         encoding = None, errors = None,
         newline = None, closefd = True) -> "IOBase":
    return text
