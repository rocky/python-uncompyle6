#  Copyright (c) 2019, 2021 by Rocky Bernstein
"""
Python 1.0 bytecode decompiler massaging.

This massages tokenized 1.0 bytecode to make it more amenable for
grammar parsing.
"""

import uncompyle6.scanners.scanner11 as scan

# bytecode verification, verify(), uses JUMP_OPs from here
from xdis.opcodes import opcode_10

JUMP_OPS = opcode_10.JUMP_OPS

# We base this off of 1.1 instead of the other way around
# because we cleaned things up this way.
# The history is that 2.7 support is the cleanest,
# then from that we got 2.6 and so on.
class Scanner10(scan.Scanner11):
    def __init__(self, show_asm=False):
        scan.Scanner11.__init__(self, show_asm)
        self.opc = opcode_10
        self.opname = opcode_10.opname
        self.version = (1, 0)
        return

    # def ingest(self, co, classname=None, code_objects={}, show_asm=None):
    #     tokens, customize = self.parent_ingest(co, classname, code_objects, show_asm)
    #     tokens = [t for t in tokens if t.kind != 'SET_LINENO']

    #     # for t in tokens:
    #     #     print(t)
    #
    #   return tokens, customize
