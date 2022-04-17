#  Copyright (c) 2015-2018, 2021-2022 by Rocky Bernstein
"""
Python 2.5 bytecode massaging.

This overlaps Python's 2.5's dis module, but it can be run from
Python 3 and other versions of Python. Also, we save token
information for later use in deparsing.
"""

import uncompyle6.scanners.scanner26 as scan

# bytecode verification, verify(), uses JUMP_OPs from here
from xdis.opcodes import opcode_25
JUMP_OPS = opcode_25.JUMP_OPS

# We base this off of 2.6 instead of the other way around
# because we cleaned things up this way.
# The history is that 2.7 support is the cleanest,
# then from that we got 2.6 and so on.
class Scanner25(scan.Scanner26):
    def __init__(self, show_asm=False):
        # There are no differences in initialization between
        # 2.5 and 2.6
        self.opc = opcode_25
        self.opname = opcode_25.opname
        scan.Scanner26.__init__(self, show_asm)
        self.version = (2, 5)
        return


if __name__ == "__main__":
    from xdis.version_info import PYTHON_VERSION_TRIPLE, version_tuple_to_str

    if PYTHON_VERSION_TRIPLE[:2] == (2, 5):
        import inspect

        co = inspect.currentframe().f_code  # type: ignore
        tokens, customize = Scanner25().ingest(co)
        for t in tokens:
            print(t.format())
        pass
    else:
        print("Need to be Python 2.5 to demo; I am version %s" % version_tuple_to_str())
