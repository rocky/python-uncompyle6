#  Copyright (c) 2019, 2021-2022 by Rocky Bernstein
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
        self.version = (1, 6)
        self.genexpr_name = '<generator expression>'
        return

    def ingest(self, co, classname=None, code_objects={}, show_asm=None):
        """
        Create "tokens" the bytecode of an Python code object. Largely these
        are the opcode name, but in some cases that has been modified to make parsing
        easier.
        returning a list of uncompyle6 Token's.

        Some transformations are made to assist the deparsing grammar:
           -  various types of LOAD_CONST's are categorized in terms of what they load
           -  COME_FROM instructions are added to assist parsing control structures
           -  operands with stack argument counts or flag masks are appended to the opcode name, e.g.:
              *  BUILD_LIST, BUILD_SET
              *  MAKE_FUNCTION and FUNCTION_CALLS append the number of positional arguments
           -  EXTENDED_ARGS instructions are removed

        Also, when we encounter certain tokens, we add them to a set which will cause custom
        grammar rules. Specifically, variable arg tokens like MAKE_FUNCTION or BUILD_LIST
        cause specific rules for the specific number of arguments they take.
        """
        tokens, customize = scan.Scanner21.ingest(self, co, classname, code_objects, show_asm)
        for t in tokens:
            if t.op == self.opc.UNPACK_LIST:
                t.kind = 'UNPACK_LIST_%d' % t.attr
            pass
        return tokens, customize
