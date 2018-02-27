#  Copyright (c) 2015-2018 by Rocky Bernstein
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
Python 3.4 bytecode decompiler scanner

Does some additional massaging of xdis-disassembled instructions to
make things easier for decompilation.

This sets up opcodes Python's 3.4 and calls a generalized
scanner routine for Python 3.
"""

from xdis.opcodes import opcode_34 as opc

# bytecode verification, verify(), uses JUMP_OPs from here
JUMP_OPS = opc.JUMP_OPS


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
