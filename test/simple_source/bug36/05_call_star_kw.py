# From 3.6 base64.py. Bug was handling *, and keyword args
def a85decode(b, *, foldspaces=False, adobe=False, ignorechars=b' \t\n\r\v'):
    return

# From 3.6 configparser.py. Same problem as above.
_UNSET = object()
def get(self, section, option, *, raw=False, vars=None, fallback=_UNSET):
    return

# From 3.6 compileall.py Bug is making default values are in quotes
def compile_command(source, filename="<input>", symbol="single"):
    return

# From 3.6 _pyio.py. Bug was in getting order of metaclass=abc.ABCMeta right
import abc
class IOBase(metaclass=abc.ABCMeta):
    pass
