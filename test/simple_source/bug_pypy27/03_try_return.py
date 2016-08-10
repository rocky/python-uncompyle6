# From PyPy 2.7 argparse.py
# PyPY reduces branches as a result of the return statement
# So we need a new rules for trystmt and try_middle which we
# suffix with _pypy, e.g. trystmt_pypy, and try_middle_pypy
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
