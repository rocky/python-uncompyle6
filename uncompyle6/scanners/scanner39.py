#  Copyright (c) 2019, 2021-2022 by Rocky Bernstein
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
"""Python 3.9 bytecode decompiler scanner.

Does some token massaging of xdis-disassembled instructions to make
things easier for decompilation.

This sets up opcodes Python's 3.9 and calls a generalized
scanner routine for Python 3.7 and up.
"""

from uncompyle6.scanners.scanner38 import Scanner38
from uncompyle6.scanners.scanner37base import Scanner37Base

# bytecode verification, verify(), uses JUMP_OPs from here
from xdis.opcodes import opcode_38 as opc

# bytecode verification, verify(), uses JUMP_OPS from here
JUMP_OPs = opc.JUMP_OPS


class Scanner39(Scanner38):
    def __init__(self, show_asm=None):
        Scanner37Base.__init__(self, (3, 9), show_asm)
        return

    pass


if __name__ == "__main__":
    print("Note: Python 3.9 decompilation not supported")
