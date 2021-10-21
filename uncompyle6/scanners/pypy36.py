#  Copyright (c) 2019 by Rocky Bernstein
"""
Python PyPy 3.6 decompiler scanner.

Does some additional massaging of xdis-disassembled instructions to
make things easier for decompilation.
"""

import uncompyle6.scanners.scanner36 as scan

# bytecode verification, verify(), uses JUMP_OPS from here
from xdis.opcodes import opcode_35 as opc  # is this right?
JUMP_OPs = opc.JUMP_OPS

# We base this off of 3.5
class ScannerPyPy36(scan.Scanner36):
    def __init__(self, show_asm):
        # There are no differences in initialization between
        # pypy 3.6 and 3.6
        scan.Scanner36.__init__(self, show_asm, is_pypy=True)
        self.version = (3, 6)
        return
