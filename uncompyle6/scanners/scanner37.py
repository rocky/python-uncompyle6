#  Copyright (c) 2016-2017 by Rocky Bernstein
"""
Python 3.7 bytecode decompiler scanner

Does some additional massaging of xdis-disassembled instructions to
make things easier for decompilation.

This sets up opcodes Python's 3.6 and calls a generalized
scanner routine for Python 3.
"""

from uncompyle6.scanners.scanner3 import Scanner3

# bytecode verification, verify(), uses JUMP_OPs from here
from xdis.opcodes import opcode_36 as opc
JUMP_OPs = opc.JUMP_OPS

class Scanner37(Scanner3):

    def __init__(self, show_asm=None):
        Scanner3.__init__(self, 3.7, show_asm)
        return
    pass

if __name__ == "__main__":
    from uncompyle6 import PYTHON_VERSION
    if PYTHON_VERSION == 3.7:
        import inspect
        co = inspect.currentframe().f_code
        tokens, customize = Scanner37().ingest(co)
        for t in tokens:
            print(t.format())
        pass
    else:
        print("Need to be Python 3.7 to demo; I am %s." %
              PYTHON_VERSION)
