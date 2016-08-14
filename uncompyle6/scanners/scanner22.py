#  Copyright (c) 2016 by Rocky Bernstein
"""
Python 2.2 bytecode scanner/deparser

This overlaps Python's 2.2's dis module, but it can be run from
Python 3 and other versions of Python. Also, we save token
information for later use in deparsing.
"""

import uncompyle6.scanners.scanner23 as scan
# from uncompyle6.scanners.scanner26 import disassemble as  disassemble26

# bytecode verification, verify(), uses JUMP_OPs from here
from xdis.opcodes import opcode_22
JUMP_OPs = opcode_22.JUMP_OPs

# We base this off of 2.3 instead of the other way around
# because we cleaned things up this way.
# The history is that 2.7 support is the cleanest,
# then from that we got 2.6 and so on.
class Scanner22(scan.Scanner23):
    def __init__(self, show_asm=False):
        scan.Scanner23.__init__(self, show_asm)
        self.opc = opcode_22
        self.opname = opcode_22.opname
        self.version = 2.2
        self.genexpr_name = '<generator expression>';
        self.parent_injest = self.disassemble
        self.disassemble = self.disassemble22
        return

    def disassemble22(self, co, classname=None, code_objects={}, show_asm=None):
        tokens, customize = self.parent_injest(co, classname, code_objects, show_asm)
        tokens = [t for t in tokens if t.type != 'SET_LINENO']
        return tokens, customize
