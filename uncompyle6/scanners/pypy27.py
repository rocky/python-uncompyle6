#  Copyright (c) 2016 by Rocky Bernstein
"""
Python PyPy 2.7 bytecode scanner/deparser

This overlaps Python's 2.7's dis module, but it can be run from
Python 3 and other versions of Python. Also, we save token
information for later use in deparsing.
"""

import uncompyle6.scanners.scanner27 as scan

# bytecode verification, verify(), uses JUMP_OPs from here
from xdis.opcodes import opcode_pypy27
JUMP_OPs = opcode_pypy27.JUMP_OPs

# We base this off of 2.6 instead of the other way around
# because we cleaned things up this way.
# The history is that 2.7 support is the cleanest,
# then from that we got 2.6 and so on.
class ScannerPyPy27(scan.Scanner27):
    def __init__(self, show_asm):
        # There are no differences in initialization between
        # pypy 2.7 and 2.7
        scan.Scanner27.__init__(self, show_asm, is_pypy=True)
        self.version = 2.7
        return
