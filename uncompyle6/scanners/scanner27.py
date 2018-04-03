# Copyright (c) 2015-2018 by Rocky Bernstein
"""
Python 2.7 bytecode ingester.

This massages tokenized 2.7 bytecode to make it more amenable for
grammar parsing.
"""


from uncompyle6.scanners.scanner2 import Scanner2

from uncompyle6 import PYTHON3
if PYTHON3:
    import sys
    intern = sys.intern

# bytecode verification, verify(), uses JUMP_OPs from here
from xdis.opcodes import opcode_27
JUMP_OPS = opcode_27.JUMP_OPs

class Scanner27(Scanner2):
    def __init__(self, show_asm=False, is_pypy=False):
        super(Scanner27, self).__init__(2.7, show_asm, is_pypy)

        # opcodes that start statements
        self.statement_opcodes = frozenset(
            self.statement_opcodes | set([
                # New in 2.7
                self.opc.SETUP_WITH,
                self.opc.STORE_SLICE_0,    self.opc.STORE_SLICE_1,
                self.opc.STORE_SLICE_2,    self.opc.STORE_SLICE_3,
                self.opc.DELETE_SLICE_0,   self.opc.DELETE_SLICE_1,
                self.opc.DELETE_SLICE_2,   self.opc.DELETE_SLICE_3,
            ]))

        # opcodes which expect a variable number pushed values and whose
        # count is in the opcode. For parsing we generally change the
        # opcode name to include that number.
        varargs_ops = set([
            self.opc.BUILD_LIST,           self.opc.BUILD_TUPLE,
            self.opc.BUILD_SLICE,          self.opc.UNPACK_SEQUENCE,
            self.opc.MAKE_FUNCTION,        self.opc.CALL_FUNCTION,
            self.opc.MAKE_CLOSURE,         self.opc.CALL_FUNCTION_VAR,
            self.opc.CALL_FUNCTION_KW,     self.opc.CALL_FUNCTION_VAR_KW,
            self.opc.DUP_TOPX,             self.opc.RAISE_VARARGS,
            # New in Python 2.7
            self.opc.BUILD_SET,            self.opc.BUILD_MAP])

        if is_pypy:
            varargs_ops.add(self.opc.CALL_METHOD)
        self.varargs_ops = frozenset(varargs_ops)

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
            self.opc.JUMP_ABSOLUTE
        ])

        self.pop_jump_if_or_pop = frozenset([self.opc.JUMP_IF_FALSE_OR_POP,
                                             self.opc.JUMP_IF_TRUE_OR_POP])

        return

    pass

if __name__ == "__main__":
    from uncompyle6 import PYTHON_VERSION
    if PYTHON_VERSION == 2.7:
        import inspect
        co = inspect.currentframe().f_code
        tokens, customize = Scanner27().ingest(co)
        for t in tokens:
            print(t)
        pass
    else:
        print("Need to be Python 2.7 to demo; I am %s." %
              PYTHON_VERSION)
