#  Copyright (c) 2015-2017, 2021-2022 by Rocky Bernstein
"""
Python 3.2 bytecode decompiler scanner.

Does some additional massaging of xdis-disassembled instructions to
make things easier for decompilation.

This sets up opcodes Python's 3.2 and calls a generalized
scanner routine for Python 3.
"""

# bytecode verification, verify(), uses JUMP_OPs from here
from xdis.opcodes import opcode_32 as opc
JUMP_OPS = opc.JUMP_OPS

from uncompyle6.scanners.scanner3 import Scanner3
class Scanner32(Scanner3):

    def __init__(self, show_asm=None, is_pypy=False):
        Scanner3.__init__(self, (3, 2), show_asm, is_pypy)
        return
    pass

if __name__ == "__main__":
    from xdis.version_info import PYTHON_VERSION_TRIPLE, version_tuple_to_str

    if PYTHON_VERSION_TRIPLE[:2] == (3, 2):
        import inspect

        co = inspect.currentframe().f_code  # type: ignore
        tokens, customize = Scanner32().ingest(co)
        for t in tokens:
            print(t.format())
        pass
    else:
        print("Need to be Python 3.2 to demo; I am version %s." % version_tuple_to_str())
