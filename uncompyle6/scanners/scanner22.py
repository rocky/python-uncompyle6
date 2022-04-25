#  Copyright (c) 2016-2018, 2021-2022 by Rocky Bernstein
"""
Python 2.2 bytecode massaging.

This massages tokenized 2.2 bytecode to make it more amenable for
grammar parsing.
"""

import uncompyle6.scanners.scanner23 as scan
# from uncompyle6.scanners.scanner26 import ingest as  ingest26

# bytecode verification, verify(), uses JUMP_OPs from here
from xdis.opcodes import opcode_22
JUMP_OPS = opcode_22.JUMP_OPS

# We base this off of 2.3 instead of the other way around
# because we cleaned things up this way.
# The history is that 2.7 support is the cleanest,
# then from that we got 2.6 and so on.
class Scanner22(scan.Scanner23):
    def __init__(self, show_asm=False):
        scan.Scanner23.__init__(self, show_asm=False)
        self.opc = opcode_22
        self.opname = opcode_22.opname
        self.version = (2, 2)
        self.genexpr_name = '<generator expression>'
        self.parent_ingest = self.ingest
        self.ingest = self.ingest22
        return

    def ingest22(self, co, classname=None, code_objects={}, show_asm=None):
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
        tokens, customize = self.parent_ingest(co, classname, code_objects, show_asm)
        tokens = [t for t in tokens if t.kind != 'SET_LINENO']
        return tokens, customize
