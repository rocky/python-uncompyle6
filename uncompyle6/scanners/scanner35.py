#  Copyright (c) 2016 by Rocky Bernstein
"""
Python 3.5 bytecode scanner/deparser

This sets up opcodes Python's 3.5 and calls a generalized
scanner routine for Python 3.
"""

from __future__ import print_function

from uncompyle6.scanners.scanner3 import Scanner3

# bytecode verification, verify(), uses JUMP_OPs from here
from xdis.opcodes import opcode_35 as opc
JUMP_OPs = map(lambda op: opc.opname[op], opc.hasjrel + opc.hasjabs)

class Scanner35(Scanner3):

    def __init__(self, show_asm=None):
        Scanner3.__init__(self, 3.5, show_asm)
        return
    pass

if __name__ == "__main__":
    from uncompyle6 import PYTHON_VERSION
    if PYTHON_VERSION == 3.5:
        import inspect
        co = inspect.currentframe().f_code
        tokens, customize = Scanner35().ingest(co)
        for t in tokens:
            print(t)
        pass
    else:
        print("Need to be Python 3.5 to demo; I am %s." %
              PYTHON_VERSION)
