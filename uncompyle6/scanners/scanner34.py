#  Copyright (c) 2015-2016 by Rocky Bernstein
"""
Python 3.4 bytecode scanner/deparser

This sets up opcodes Python's 3.4 and calls a generalized
scanner routine for Python 3.
"""

from xdis.opcodes import opcode_34 as opc

# bytecode verification, verify(), uses JUMP_OPs from here
JUMP_OPs = map(lambda op: opc.opname[op], opc.hasjrel + opc.hasjabs)


from uncompyle6.scanners.scanner3 import Scanner3
class Scanner34(Scanner3):

    def __init__(self, show_asm=None):
        Scanner3.__init__(self, 3.4, show_asm)
        return
    pass

if __name__ == "__main__":
    from uncompyle6 import PYTHON_VERSION
    if PYTHON_VERSION == 3.4:
        import inspect
        co = inspect.currentframe().f_code
        tokens, customize = Scanner34().ingest(co)
        for t in tokens:
            print(t)
        pass
    else:
        print("Need to be Python 3.4 to demo; I am %s." %
              PYTHON_VERSION)
