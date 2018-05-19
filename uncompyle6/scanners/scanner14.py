#  Copyright (c) 2018 by Rocky Bernstein
"""
Python 1.4 bytecode decompiler massaging.

This massages tokenized 1.4 bytecode to make it more amenable for
grammar parsing.
"""

import uncompyle6.scanners.scanner15 as scan
# from uncompyle6.scanners.scanner26 import ingest as  ingest26

# bytecode verification, verify(), uses JUMP_OPs from here
from xdis.opcodes import opcode_14
JUMP_OPS = opcode_14.JUMP_OPS

# We base this off of 1.5 instead of the other way around
# because we cleaned things up this way.
# The history is that 2.7 support is the cleanest,
# then from that we got 2.6 and so on.
class Scanner14(scan.Scanner15):
    def __init__(self, show_asm=False):
        scan.Scanner15.__init__(self, show_asm)
        self.opc = opcode_14
        self.opname = opcode_14.opname
        self.version = 1.4
        self.genexpr_name = '<generator expression>'
        return
