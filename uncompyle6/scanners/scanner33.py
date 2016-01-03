#  Copyright (c) 2015-2016 by Rocky Bernstein
"""
Python 3 bytecode scanner/deparser

This overlaps Python's 3.3's dis module, but it can be run from
Python 2 and other versions of Python. Also, we save token information
for later use in deparsing.
"""

from __future__ import print_function

import uncompyle6.scanners.scanner3 as scan3

import uncompyle6.opcodes.opcode_33
# verify uses JUMP_OPs from here
JUMP_OPs = uncompyle6.opcodes.opcode_33.JUMP_OPs

class Scanner33(scan3.Scanner3):

    def disassemble(self, co, classname=None, code_objects={}):
        return self.disassemble_generic(co, classname, code_objects=code_objects)

if __name__ == "__main__":
    import inspect
    co = inspect.currentframe().f_code
    tokens, customize = Scanner33(3.3).disassemble(co)
    for t in tokens:
        print(t)
    pass
