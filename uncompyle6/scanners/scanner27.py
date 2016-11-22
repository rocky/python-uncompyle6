# Copyright (c) 2015, 2016 by Rocky Bernstein
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
JUMP_OPs = opcode_27.JUMP_OPs

class Scanner27(Scanner2):
    def __init__(self, show_asm=False, is_pypy=False):
        super(Scanner27, self).__init__(2.7, show_asm, is_pypy)

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

        # opcodes with expect a variable number pushed values whose
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

    def patch_continue(self, tokens, offset, op):
        if op in (self.opc.JUMP_FORWARD, self.opc.JUMP_ABSOLUTE):
            # FIXME: this is a hack to catch stuff like:
            #   for ...
            #     try: ...
            #     except: continue
            # the "continue" is not on a new line.
            n = len(tokens)
            if (n > 2 and
                tokens[-1].type == 'JUMP_BACK' and
                self.code[offset+3] == self.opc.END_FINALLY):
                tokens[-1].type = intern('CONTINUE')

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
