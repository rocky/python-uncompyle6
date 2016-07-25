#  Copyright (c) 2016 by Rocky Bernstein
"""
Python PyPy 3.2 bytecode scanner/deparser

This overlaps Python's 3.2's dis module, but it can be run from
Python 3 and other versions of Python. Also, we save token
information for later use in deparsing.
"""

import uncompyle6.scanners.scanner32 as scan

# bytecode verification, verify(), uses JUMP_OPs from here
from xdis.opcodes import opcode_32 as opc  # is this rgith?
JUMP_OPs = map(lambda op: opc.opname[op], opc.hasjrel + opc.hasjabs)

# We base this off of 2.6 instead of the other way around
# because we cleaned things up this way.
# The history is that 2.7 support is the cleanest,
# then from that we got 2.6 and so on.
class ScannerPyPy32(scan.Scanner32):
    def __init__(self, show_asm):
        # There are no differences in initialization between
        # pypy 3.2 and 3.2
        scan.Scanner32.__init__(self, show_asm, is_pypy=True)
        self.version = 3.2
        return
