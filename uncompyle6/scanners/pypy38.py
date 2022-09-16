#  Copyright (c) 2021-2022 by Rocky Bernstein
"""
Python PyPy 3.8 decompiler scanner.

Does some additional massaging of xdis-disassembled instructions to
make things easier for decompilation.
"""

import uncompyle6.scanners.scanner38 as scan

# bytecode verification, verify(), uses JUMP_OPS from here
from xdis.opcodes import opcode_38pypy as opc

JUMP_OPs = opc.JUMP_OPS


# We base this off of 3.8
class ScannerPyPy38(scan.Scanner38):
    def __init__(self, show_asm):
        # There are no differences in initialization between
        # pypy 3.8 and 3.8
        scan.Scanner38.__init__(self, show_asm, is_pypy=True)
        self.version = (3, 8)
        self.opc = opc
        return
