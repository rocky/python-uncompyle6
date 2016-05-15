#  Copyright (c) 2015-2016 by Rocky Bernstein
"""
Python 3.4 bytecode scanner/deparser

This sets up opcodes Python's 3.5 and calls a generalized
scanner routine for Python 3.
"""

from __future__ import print_function

import uncompyle6.scanners.scanner3 as scan3
from uncompyle6.opcodes.opcode_34 import opname as opnames

# bytecode verification, verify(), uses JUMP_OPs from here
from uncompyle6.opcodes.opcode_34 import JUMP_OPs

class Scanner34(scan3.Scanner3):
    def disassemble(self, co, classname=None, code_objects={}):
        return self.disassemble3(co, opnames, classname, code_objects)

if __name__ == "__main__":
    import inspect
    co = inspect.currentframe().f_code
    tokens, customize = Scanner34(3.4).disassemble(co)
    for t in tokens:
        print(t)
    pass
