# From python 3.4 endian.py
# Bug was having two CALL_FUNCTION ops in bytecode.
from ctypes import *
class _swapped_meta(type(Structure)):
    pass
