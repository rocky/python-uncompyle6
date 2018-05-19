#  Copyright (c) 2016-2018 by Rocky Bernstein
"""
Python 2.3 bytecode massaging.

This massages tokenized 2.3 bytecode to make it more amenable for
grammar parsing.
"""

import uncompyle6.scanners.scanner24 as scan

# bytecode verification, verify(), uses JUMP_OPs from here
from xdis.opcodes import opcode_23
JUMP_OPS = opcode_23.JUMP_OPS

# We base this off of 2.4 instead of the other way around
# because we cleaned things up this way.
# The history is that 2.7 support is the cleanest,
# then from that we got 2.6 and so on.
class Scanner23(scan.Scanner24):
    def __init__(self, show_asm=False):
        scan.Scanner24.__init__(self, show_asm)
        self.opc = opcode_23
        self.opname = opcode_23.opname
        # These are the only differences in initialization between
        # 2.3-2.6
        self.version = 2.3
        self.genexpr_name = '<generator expression>'
        return
