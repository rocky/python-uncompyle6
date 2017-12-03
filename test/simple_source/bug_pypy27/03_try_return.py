# From PyPy 2.7 argparse.py
# PyPY reduces branches as a result of the return statement
# So we need a new rules for try_except and except_handler which we
# suffix with _pypy, e.g. try_except_pypy, and except_handler_pypy
def call(self, string):
    try:
        return open(string, self, self._bufsize)
    except IOError:
        pass

# From PyPy 2.6.1 function.py
def _call_funcptr(self, funcptr, *newargs):
    try:
        return self._build_result(self._restype_, result)
    finally:
        funcptr.free_temp_buffers()
