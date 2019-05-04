#  Copyright (c) 2019 by Rocky Bernstein
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
Python 3.8 bytecode decompiler scanner

Does some additional massaging of xdis-disassembled instructions to
make things easier for decompilation.

This sets up opcodes Python's 3.8 and calls a generalized
scanner routine for Python 3.
"""

from uncompyle6.scanners.scanner37 import Scanner37
from uncompyle6.scanners.scanner3 import Scanner3

# bytecode verification, verify(), uses JUMP_OPs from here
from xdis.opcodes import opcode_38 as opc
JUMP_OPs = opc.JUMP_OPS

class Scanner38(Scanner37):

    def __init__(self, show_asm=None):
        Scanner3.__init__(self, 3.8, show_asm)
        return
    pass

if __name__ == "__main__":
    from uncompyle6 import PYTHON_VERSION
    if PYTHON_VERSION == 3.8:
        import inspect
        co = inspect.currentframe().f_code
        tokens, customize = Scanner38().ingest(co)
        for t in tokens:
            print(t.format())
        pass
    else:
        print("Need to be Python 3.8 to demo; I am %s." %
              PYTHON_VERSION)
