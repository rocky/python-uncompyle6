#  Copyright (c) 2019-2022, 2024 by Rocky Bernstein
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
Python 3.8 bytecode decompiler scanner.

Does some additional massaging of xdis-disassembled instructions to
make things easier for decompilation.

This sets up opcodes Python's 3.8 and calls a generalized
scanner routine for Python 3.7 and up.
"""

from typing import Dict, Tuple

# bytecode verification, verify(), uses JUMP_OPs from here
from xdis.opcodes import opcode_38 as opc

from uncompyle6.scanners.scanner37 import Scanner37
from uncompyle6.scanners.scanner37base import Scanner37Base
from uncompyle6.scanners.tok import off2int

# bytecode verification, verify(), uses JUMP_OPS from here
JUMP_OPs = opc.JUMP_OPS


class Scanner38(Scanner37):
    def __init__(self, show_asm=None, debug="", is_pypy=False):
        Scanner37Base.__init__(self, (3, 8), show_asm, debug, is_pypy)
        self.debug = debug
        return

    pass

    def ingest(
        self, bytecode, classname=None, code_objects={}, show_asm=None
    ) -> Tuple[list, dict]:
        """
        Create "tokens" the bytecode of an Python code object. Largely these
        are the opcode name, but in some cases that has been modified to make parsing
        easier.
        returning a list of uncompyle6 Token's.

        Some transformations are made to assist the deparsing grammar:
           -  various types of LOAD_CONST's are categorized in terms of what they load
           -  COME_FROM instructions are added to assist parsing control structures
           -  operands with stack argument counts or flag masks are appended to the opcode name, e.g.:
              *  BUILD_LIST, BUILD_SET
              *  MAKE_FUNCTION and FUNCTION_CALLS append the number of positional arguments
           -  EXTENDED_ARGS instructions are removed

        Also, when we encounter certain tokens, we add them to a set which will cause custom
        grammar rules. Specifically, variable arg tokens like MAKE_FUNCTION or BUILD_LIST
        cause specific rules for the specific number of arguments they take.
        """
        tokens, customize = super(Scanner38, self).ingest(
            bytecode, classname, code_objects, show_asm
        )

        # Hacky way to detect loop ranges.
        # The key in jump_back_targets is the start of the loop.
        # The value is where the loop ends. In current Python,
        # JUMP_BACKS are always to loops. And blocks are ordered so that the
        # JUMP_BACK with the highest offset will be where the range ends.
        jump_back_targets: Dict[int, int] = {}
        for token in tokens:
            if token.kind == "JUMP_BACK":
                jump_back_targets[token.attr] = token.offset
                pass
            pass

        if self.debug and jump_back_targets:
            print(jump_back_targets)
        loop_ends = []
        next_end = tokens[len(tokens) - 1].off2int() + 10

        new_tokens = []
        for i, token in enumerate(tokens):
            opname = token.kind
            offset = token.offset
            if offset == next_end:
                loop_ends.pop()
                if self.debug:
                    print(f"{'  ' * len(loop_ends)}remove loop offset {offset}")
                    pass
                next_end = (
                    loop_ends[-1]
                    if len(loop_ends)
                    else tokens[len(tokens) - 1].off2int() + 10
                )

            # things that smash new_tokens like BUILD_LIST have to come first.

            if offset in jump_back_targets:
                next_end = off2int(jump_back_targets[offset], prefer_last=False)
                if self.debug:
                    print(
                        f"{'  ' * len(loop_ends)}adding loop offset {offset} ending at {next_end}"
                    )
                loop_ends.append(next_end)

            # Turn JUMP opcodes into "BREAK_LOOP" opcodes.
            # FIXME!!!!: this should be replaced by proper control flow.
            if opname in ("JUMP_FORWARD", "JUMP_ABSOLUTE") and len(loop_ends):
                jump_target = token.attr

                if opname == "JUMP_ABSOLUTE" and jump_target <= next_end:
                    # Not a forward-enough jump to break out of the next loop, so continue.
                    # FIXME: Do we need "continue" detection?
                    new_tokens.append(token)
                    continue

                j = i
                while tokens[j - 1] in ("POP_TOP", "POP_BLOCK", "POP_EXCEPT"):
                    j -= 1
                    if tokens[j].linestart:
                        break
                token_with_linestart = tokens[j]

                if token_with_linestart.linestart:
                    token.kind = "BREAK_LOOP"

                pass
            new_tokens.append(token)

        if show_asm in ("both", "after"):
            print("\n# ---- tokenization:")
            # FIXME: t.format() is changing tokens!
            for t in new_tokens.copy():
                print(t.format(line_prefix=""))
            print()

        return new_tokens, customize


if __name__ == "__main__":
    from xdis.version_info import PYTHON_VERSION_TRIPLE, version_tuple_to_str

    if PYTHON_VERSION_TRIPLE[:2] == (3, 8):
        import inspect

        co = inspect.currentframe().f_code  # type: ignore
        tokens, customize = Scanner38().ingest(co)
        for t in tokens:
            print(t.format())
        pass
    else:
        print(f"Need to be Python 3.8 to demo; I am version {version_tuple_to_str()}.")
