#  Copyright (c) 2016 by Rocky Bernstein
"""
Python 3.5 bytecode scanner/deparser

This sets up opcodes Python's 3.5 and calls a generalized
scanner routine for Python 3.
"""

from __future__ import print_function

from uncompyle6.scanners.scanner3 import Scanner3

# bytecode verification, verify(), uses JUMP_OPs from here
from uncompyle6.opcodes.opcode_35 import JUMP_OPs

class Scanner35(Scanner3):

    def __init__(self):
        super(Scanner3, self).__init__(3.5)

    def disassemble(self, co, classname=None, code_objects={}):
        return self.disassemble3(co, classname, code_objects)

    def disassemble_native(self, co, classname=None, code_objects={}):
        return self.disassemble3_native(co, classname, code_objects)

if __name__ == "__main__":
    from uncompyle6 import PYTHON_VERSION
    if PYTHON_VERSION == 3.5:
        import inspect
        co = inspect.currentframe().f_code
        tokens, customize = Scanner35(3.5).disassemble(co)
        for t in tokens:
            print(t.format())
        pass
    else:
        print("Need to be Python 3.5to demo; I am %s." %
              PYTHON_VERSION)
