# Copyright (c) 2015, 2016 by Rocky Bernstein
"""
Python 2.7 bytecode scanner/deparser

This overlaps Python's 2.7's dis module, but it can be run from
Python 3 and other versions of Python. Also, we save token information
for later use in deparsing.
"""


from __future__ import print_function

from uncompyle6.scanners.scanner2 import Scanner2

# bytecode verification, verify(), uses JUMP_OPs from here
from xdis.opcodes import opcode_27
JUMP_OPs = opcode_27.JUMP_OPs

class Scanner27(Scanner2):
    def __init__(self):
        super(Scanner27, self).__init__(2.7)
        return
    pass

if __name__ == "__main__":
    from uncompyle6 import PYTHON_VERSION
    if PYTHON_VERSION == 2.7:
        import inspect
        co = inspect.currentframe().f_code
        tokens, customize = Scanner27().disassemble(co)
        for t in tokens:
            print(t.format())
        pass
    else:
        print("Need to be Python 2.7 to demo; I am %s." %
              PYTHON_VERSION)
