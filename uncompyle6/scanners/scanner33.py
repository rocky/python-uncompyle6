#  Copyright (c) 2015-2016 by Rocky Bernstein
"""
Python 3.3 bytecode scanner/deparser

This sets up opcodes Python's 3.3 and calls a generalized
scanner routine for Python 3.
"""

from __future__ import print_function

import uncompyle6

# bytecode verification, verify(), uses JUMP_OPs from here
JUMP_OPs = uncompyle6.opcodes.opcode_33.JUMP_OPs

from uncompyle6.scanners.scanner3 import Scanner3
class Scanner33(Scanner3):

    def __init__(self):
        super(Scanner3, self).__init__(3.3)
        self.showast = False

    def disassemble(self, co, classname=None, code_objects={}, showast=False):
        return self.disassemble_generic(co, classname, code_objects=code_objects)

    def disassemble_native(self, co, classname=None, code_objects={}):
        return self.disassemble3_native(co, classname, code_objects)

if __name__ == "__main__":
    from uncompyle6 import PYTHON_VERSION
    if PYTHON_VERSION == 3.3:
        import inspect
        co = inspect.currentframe().f_code
        tokens, customize = Scanner33().disassemble(co)
        for t in tokens:
            print(t)
        pass
    else:
        print("Need to be Python 3.3 to demo; I am %s." %
              PYTHON_VERSION)
