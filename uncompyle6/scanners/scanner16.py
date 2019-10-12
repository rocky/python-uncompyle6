#  Copyright (c) 2019 by Rocky Bernstein
"""
Python 1.6 bytecode decompiler massaging.

This massages tokenized 1.6 bytecode to make it more amenable for
grammar parsing.
"""

import uncompyle6.scanners.scanner21 as scan
# from uncompyle6.scanners.scanner26 import ingest as  ingest26

# bytecode verification, verify(), uses JUMP_OPs from here
from xdis.opcodes import opcode_16
JUMP_OPS = opcode_16.JUMP_OPS

# We base this off of 2.2 instead of the other way around
# because we cleaned things up this way.
# The history is that 2.7 support is the cleanest,
# then from that we got 2.6 and so on.
class Scanner16(scan.Scanner21):
    def __init__(self, show_asm=False):
        scan.Scanner21.__init__(self, show_asm)
        self.opc = opcode_16
        self.opname = opcode_16.opname
        self.version = 1.6
        self.genexpr_name = '<generator expression>'
        return

    def ingest(self, co, classname=None, code_objects={}, show_asm=None):
        """
        Pick out tokens from an uncompyle6 code object, and transform them,
        returning a list of uncompyle6 Token's.

        The transformations are made to assist the deparsing grammar.
        """
        tokens, customize = scan.Scanner21.ingest(self, co, classname, code_objects, show_asm)
        for t in tokens:
            if t.op == self.opc.UNPACK_LIST:
                t.kind = 'UNPACK_LIST_%d' % t.attr
            pass
        return tokens, customize
