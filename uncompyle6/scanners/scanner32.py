#  Copyright (c) 2015 by Rocky Bernstein
"""
Python 3.2 bytecode scanner/deparser

This overlaps Python's 3.2's dis module, but it can be run from
Python 2 and other versions of Python. Also, we save token information
for later use in deparsing.
"""

from __future__ import print_function

import uncompyle6.scanners.scanner33 as scan33
import uncompyle6.scanner as scan

class Scanner32(scan.Scanner):
    def __init__(self):
        scan.Scanner.__init__(self, 3.2) # check

    def disassemble(self, co, classname=None):
        return scan33.Scanner33().disassemble(co, classname)

if __name__ == "__main__":
    co = inspect.currentframe().f_code
    tokens, customize = Scanner33().disassemble(co)
    for t in tokens:
        print(t)
    pass
