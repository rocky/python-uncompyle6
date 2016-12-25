#  Copyright (c) 2016 by Rocky Bernstein
"""
Python 1.5 bytecode scanner/deparser

This massages tokenized 1.5 bytecode to make it more amenable for
grammar parsing.
"""

import uncompyle6.scanners.scanner21 as scan
# from uncompyle6.scanners.scanner26 import ingest as  ingest26

# bytecode verification, verify(), uses JUMP_OPs from here
from xdis.opcodes import opcode_15
JUMP_OPs = opcode_15.JUMP_OPs

# We base this off of 2.1 instead of the other way around
# because we cleaned things up this way.
# The history is that 2.7 support is the cleanest,
# then from that we got 2.6 and so on.
class Scanner15(scan.Scanner21):
    def __init__(self, show_asm=False):
        scan.Scanner21.__init__(self, show_asm=False)
        self.opc = opcode_15
        self.opname = opcode_15.opname
        self.version = 1.5
        self.genexpr_name = '<generator expression>'
        return
