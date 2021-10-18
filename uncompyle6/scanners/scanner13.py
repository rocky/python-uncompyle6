#  Copyright (c) 2018-2019, 2021 by Rocky Bernstein
"""
Python 1.3 bytecode decompiler massaging.

This massages tokenized 1.3 bytecode to make it more amenable for
grammar parsing.
"""

import uncompyle6.scanners.scanner14 as scan

# from uncompyle6.scanners.scanner26 import ingest as  ingest26

# bytecode verification, verify(), uses JUMP_OPs from here
from xdis.opcodes import opcode_13

JUMP_OPS = opcode_13.JUMP_OPS

# We base this off of 1.4 instead of the other way around
# because we cleaned things up this way.
# The history is that 2.7 support is the cleanest,
# then from that we got 2.6 and so on.
class Scanner13(scan.Scanner14):
    def __init__(self, show_asm=False):
        scan.Scanner14.__init__(self, show_asm)
        self.opc = opcode_13
        self.opname = opcode_13.opname
        self.version = (1, 3)
        return

    # def ingest(self, co, classname=None, code_objects={}, show_asm=None):
    #     tokens, customize = self.parent_ingest(co, classname, code_objects, show_asm)
    #     tokens = [t for t in tokens if t.kind != 'SET_LINENO']

    #     # for t in tokens:
    #     #     print(t)
    #
    #   return tokens, customize
