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
"""Python 3.8 bytecode decompiler scanner

Does some token massaging of xdis-disassembled instructions to make
things easier for decompilation.

This sets up opcodes Python's 3.8 and calls a generalized
scanner routine for Python 3.7 and up.
"""

from uncompyle6.scanners.scanner37 import Scanner37
from uncompyle6.scanners.scanner37base import Scanner37Base

# bytecode verification, verify(), uses JUMP_OPs from here
from xdis.opcodes import opcode_38 as opc

# bytecode verification, verify(), uses JUMP_OPS from here
JUMP_OPs = opc.JUMP_OPS


class Scanner38(Scanner37):
    def __init__(self, show_asm=None):
        Scanner37Base.__init__(self, 3.8, show_asm)
        return

    pass

    def ingest(self, co, classname=None, code_objects={}, show_asm=None):
        tokens, customize = super(Scanner38, self).ingest(
            co, classname, code_objects, show_asm
        )
        for i, token in enumerate(tokens):
            opname = token.kind
            if opname in ("JUMP_FORWARD", "JUMP_ABSOLUTE"):
                # Turn JUMPs into BREAK_LOOP
                jump_target = token.attr

                if opname == "JUMP_ABSOLUTE" and token.offset >= jump_target:
                    # Not a forward jump, so continue
                    # FIXME: Do we need "continue" detection?
                    continue
                if i + 1 < len(tokens) and tokens[i + 1] == "JUMP_BACK":
                    # Sometimes the jump back is *after* the break...
                    jump_back_index = i + 1
                else:
                    # and sometimes it is *before* where we jumped to.
                    jump_back_index = self.offset2tok_index[jump_target] - 1
                    while tokens[jump_back_index].kind.startswith("COME_FROM_"):
                        jump_back_index -= 1
                        pass
                    pass
                jump_back_token = tokens[jump_back_index]
                if (
                    jump_back_token == "JUMP_BACK"
                    and jump_back_token.attr < token.offset
                ):
                    token.kind = "BREAK_LOOP"
                pass
            pass
        return tokens, customize


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
