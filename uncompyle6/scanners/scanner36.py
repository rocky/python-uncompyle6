#  Copyright (c) 2016-2017 by Rocky Bernstein
"""
Python 3.6 bytecode scanner/deparser

This sets up opcodes Python's 3.6 and calls a generalized
scanner routine for Python 3.
"""

from uncompyle6.scanners.scanner3 import Scanner3

# bytecode verification, verify(), uses JUMP_OPs from here
from xdis.opcodes import opcode_36 as opc
JUMP_OPs = map(lambda op: opc.opname[op], opc.hasjrel + opc.hasjabs)

class Scanner36(Scanner3):

    def __init__(self, show_asm=None):
        Scanner3.__init__(self, 3.6, show_asm)
        return

    def ingest(self, co, classname=None, code_objects={}, show_asm=None):
        tokens, customize = Scanner3.ingest(self, co, classname, code_objects, show_asm)
        for t in tokens:
            # The lowest bit of flags indicates whether the
            # var-keyword argument is placed at the top of the stack
            if t.op == self.opc.CALL_FUNCTION_EX and t.attr & 1:
                t.type = 'CALL_FUNCTION_EX_KW'
                pass
            elif t.op == self.opc.CALL_FUNCTION_KW:
                t.type = 'CALL_FUNCTION_KW_{t.attr}'.format(**locals())
            elif t.op == self.opc.BUILD_TUPLE_UNPACK_WITH_CALL:
                t.type = 'BUILD_TUPLE_UNPACK_WITH_CALL_%d' % t.attr
            elif t.op == self.opc.BUILD_MAP_UNPACK_WITH_CALL:
                t.type = 'BUILD_MAP_UNPACK_WITH_CALL_%d' % t.attr
            pass
        return tokens, customize

    pass

if __name__ == "__main__":
    from uncompyle6 import PYTHON_VERSION
    if PYTHON_VERSION == 3.6:
        import inspect
        co = inspect.currentframe().f_code
        tokens, customize = Scanner36().ingest(co)
        for t in tokens:
            print(t.format())
        pass
    else:
        print("Need to be Python 3.6 to demo; I am %s." %
              PYTHON_VERSION)
