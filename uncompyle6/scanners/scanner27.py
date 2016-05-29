# Copyright (c) 2015, 2016 by Rocky Bernstein
"""
Python 2.7 bytecode scanner/deparser

This overlaps Python's 2.7's dis module, but it can be run from
Python 3 and other versions of Python. Also, we save token information
for later use in deparsing.
"""


from __future__ import print_function

from uncompyle6.scanners.scanner2 import Scanner2

# bytecode verification, verify(), uses JUMP_OPs from here
from xdis.opcodes import opcode_27
JUMP_OPs = opcode_27.JUMP_OPs

class Scanner27(Scanner2):
    def __init__(self):
        super(Scanner27, self).__init__(2.7)

        # opcodes that start statements
        self.stmt_opcodes = frozenset([
            self.opc.SETUP_LOOP,       self.opc.BREAK_LOOP,
            self.opc.SETUP_FINALLY,    self.opc.END_FINALLY,
            self.opc.SETUP_EXCEPT,
            self.opc.POP_BLOCK,        self.opc.STORE_FAST, self.opc.DELETE_FAST,
            self.opc.STORE_DEREF,      self.opc.STORE_GLOBAL,
            self.opc.DELETE_GLOBAL,    self.opc.STORE_NAME,
            self.opc.DELETE_NAME,      self.opc.STORE_ATTR,
            self.opc.DELETE_ATTR,      self.opc.STORE_SUBSCR,
            self.opc.DELETE_SUBSCR,    self.opc.RETURN_VALUE,
            self.opc.RAISE_VARARGS,    self.opc.POP_TOP,
            self.opc.PRINT_EXPR,       self.opc.PRINT_ITEM,
            self.opc.PRINT_NEWLINE,    self.opc.PRINT_ITEM_TO,
            self.opc.PRINT_NEWLINE_TO, self.opc.CONTINUE_LOOP,
            self.opc.JUMP_ABSOLUTE,    self.opc.EXEC_STMT,
            # New in 2.7
            self.opc.SETUP_WITH,
            self.opc.STORE_SLICE_0,    self.opc.STORE_SLICE_1,
            self.opc.STORE_SLICE_2,    self.opc.STORE_SLICE_3,
            self.opc.DELETE_SLICE_0,   self.opc.DELETE_SLICE_1,
            self.opc.DELETE_SLICE_2,   self.opc.DELETE_SLICE_3,
        ])

        # "setup" opcodes
        self.setup_ops = frozenset([
            self.opc.SETUP_EXCEPT, self.opc.SETUP_FINALLY,
            # New in 2.7
            self.opc.SETUP_WITH])

        # opcodes that store values into a variable
        self.designator_ops = frozenset([
            self.opc.STORE_FAST,    self.opc.STORE_NAME,
            self.opc.STORE_GLOBAL,  self.opc.STORE_DEREF,   self.opc.STORE_ATTR,
            self.opc.STORE_SLICE_0, self.opc.STORE_SLICE_1, self.opc.STORE_SLICE_2,
            self.opc.STORE_SLICE_3, self.opc.STORE_SUBSCR,  self.opc.UNPACK_SEQUENCE,
            self.opc.JA
        ])
        return
    pass

if __name__ == "__main__":
    from uncompyle6 import PYTHON_VERSION
    if PYTHON_VERSION == 2.7:
        import inspect
        co = inspect.currentframe().f_code
        tokens, customize = Scanner27().disassemble(co)
        for t in tokens:
            print(t.format())
        pass
    else:
        print("Need to be Python 2.7 to demo; I am %s." %
              PYTHON_VERSION)
