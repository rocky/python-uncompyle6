#  Copyright (c) 2018, 2024 by Rocky Bernstein
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

from uncompyle6.semantics.fragments import (
    FragmentsWalker,
    code_deparse as fragments_code_deparse,
)
from uncompyle6.semantics.pysource import SourceWalker, code_deparse


# FIXME: does this handle nested code, and lambda properly
class LineMapWalker(SourceWalker):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.source_linemap = {}
        self.current_line_number = 1

    def write(self, *data):
        """Augment write routine to keep track of current line."""
        for line in data:
            # print(f"XXX write: '{line}'")
            for i in str(line):
                if i == "\n":
                    self.current_line_number += 1
                    pass
                pass
            pass
        return super().write(*data)

    # Note n_expr needs treatment too

    def default(self, node):
        """Augment default-write routine to record line number changes."""
        if hasattr(node, "linestart"):
            if node.linestart:
                self.source_linemap[self.current_line_number] = node.linestart
        return super().default(node)

    def n_LOAD_CONST(self, node):
        if hasattr(node, "linestart"):
            if node.linestart:
                self.source_linemap[self.current_line_number] = node.linestart
        return super().n_LOAD_CONST(node)


class LineMapFragmentWalker(LineMapWalker, FragmentsWalker):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


def deparse_code_with_map(*args, **kwargs):
    """
    Like deparse_code but saves line number correspondences.
    Deprecated. Use code_deparse_with_map
    """
    kwargs["walker"] = LineMapWalker
    return code_deparse(*args, **kwargs)


def code_deparse_with_map(*args, **kwargs):
    """
    Like code_deparse but saves line number correspondences.
    """
    kwargs["walker"] = LineMapWalker
    return code_deparse(*args, **kwargs)


def code_deparse_with_fragments_and_map(*args, **kwargs):
    """
    Like code_deparse_with_map but saves fragments.
    """
    kwargs["walker"] = LineMapFragmentWalker
    return fragments_code_deparse(*args, **kwargs)


if __name__ == "__main__":

    def deparse_test(co):
        """This is a docstring"""
        deparsed = code_deparse_with_map(co)
        a = 1
        b = 2
        print("\n")
        linemap = [
            (line_no, deparsed.source_linemap[line_no])
            for line_no in sorted(deparsed.source_linemap.keys())
        ]
        print(linemap)
        deparsed = code_deparse_with_fragments_and_map(co)
        print("\n")
        linemap2 = [
            (line_no, deparsed.source_linemap[line_no])
            for line_no in sorted(deparsed.source_linemap.keys())
        ]
        print(linemap2)
        # assert linemap == linemap2
        return

    deparse_test(deparse_test.func_code)
