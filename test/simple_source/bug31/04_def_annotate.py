# Bug in 3.1 _pyio.py. The -> "IOBase" is problematic

def open(file, mode = "r", buffering = None,
         encoding = None, errors = None,
         newline = None, closefd = True) -> "IOBase":
    return text
