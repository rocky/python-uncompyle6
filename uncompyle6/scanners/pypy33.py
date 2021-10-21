#  Copyright (c) 2019-2021 by Rocky Bernstein
"""
Python PyPy 3.3 decompiler scanner.

Does some additional massaging of xdis-disassembled instructions to
make things easier for decompilation.
"""

import uncompyle6.scanners.scanner33 as scan

# bytecode verification, verify(), uses JUMP_OPs from here
from xdis.opcodes import opcode_33pypy as opc

JUMP_OPs = map(lambda op: opc.opname[op], opc.hasjrel + opc.hasjabs)

# We base this off of 3.3
class ScannerPyPy33(scan.Scanner33):
    def __init__(self, show_asm):
        # There are no differences in initialization between
        # pypy 3.3 and 3.3
        scan.Scanner33.__init__(self, show_asm, is_pypy=True)
        self.version = (3, 3)
        self.opc = opc
        return
