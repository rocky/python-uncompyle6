#  Copyright (c) 2016-2018, 2021 by Rocky Bernstein
"""
Python 2.1 bytecode massaging.

This massages tokenized 2.1 bytecode to make it more amenable for
grammar parsing.
"""

import uncompyle6.scanners.scanner22 as scan
# from uncompyle6.scanners.scanner26 import ingest as  ingest26

# bytecode verification, verify(), uses JUMP_OPs from here
from xdis.opcodes import opcode_21
JUMP_OPS = opcode_21.JUMP_OPS

# We base this off of 2.2 instead of the other way around
# because we cleaned things up this way.
# The history is that 2.7 support is the cleanest,
# then from that we got 2.6 and so on.
class Scanner21(scan.Scanner22):
    def __init__(self, show_asm=False):
        scan.Scanner22.__init__(self, show_asm)
        self.opc = opcode_21
        self.opname = opcode_21.opname
        self.version = (2, 1)
        self.genexpr_name = '<generator expression>'
        return
