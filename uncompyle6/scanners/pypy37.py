#  Copyright (c) 2021-2022 by Rocky Bernstein
"""
Python PyPy 3.7 decompiler scanner.

Does some additional massaging of xdis-disassembled instructions to
make things easier for decompilation.
"""

import uncompyle6.scanners.scanner37 as scan

# bytecode verification, verify(), uses JUMP_OPS from here
from xdis.opcodes import opcode_37pypy as opc  # is this right?

JUMP_OPs = opc.JUMP_OPS


# We base this off of 3.7
class ScannerPyPy37(scan.Scanner37):
    def __init__(self, show_asm):
        # There are no differences in initialization between
        # pypy 3.7 and 3.7
        scan.Scanner37.__init__(self, show_asm, is_pypy=True)
        self.version = (3, 7)
        self.opc = opc
        self.is_pypy = True
        return
