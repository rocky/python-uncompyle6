#  Copyright (c) 2015-2016 by Rocky Bernstein
"""
Python 3.2 bytecode scanner/deparser

This overlaps various Python3.2's dis module, but it can be run from
Python versions other than the version running this code. Notably,
run from Python version 2. See doc comments in scanner3.py for more information.
"""

from __future__ import print_function

import uncompyle6.scanners.scanner3 as scan3

import uncompyle6.opcodes.opcode_32
# verify uses JUMP_OPs from here
JUMP_OPs = uncompyle6.opcodes.opcode_32.JUMP_OPs

class Scanner32(scan3.Scanner3):

    def disassemble(self, co, classname=None, code_objects={}):
        return self.disassemble_generic(co, classname, code_objects=code_objects)

if __name__ == "__main__":
    import inspect
    co = inspect.currentframe().f_code
    tokens, customize = Scanner32(3.2).disassemble(co)
    for t in tokens:
        print(t)
    pass
