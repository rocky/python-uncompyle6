#  Copyright (c) 2018 by Rocky Bernstein
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
from uncompyle6.semantics.pysource import SourceWalker, code_deparse
import uncompyle6.semantics.fragments as fragments

# FIXME: does this handle nested code, and lambda properly
class LineMapWalker(SourceWalker):
    def __init__(self, *args, **kwargs):
        super(LineMapWalker, self).__init__(*args, **kwargs)
        self.source_linemap = {}
        self.current_line_number = 1

    def write(self, *data):
        """Augment write routine to keep track of current line"""
        for l in data:
            ## print("XXX write: '%s'" % l)
            for i in str(l):
                if i == '\n':
                    self.current_line_number += 1
                    pass
                pass
            pass
        return super(LineMapWalker, self).write(*data)

    # Note n_expr needs treatment too

    def default(self, node):
        """Augment write default routine to record line number changes"""
        if hasattr(node, 'linestart'):
            if node.linestart:
                self.source_linemap[self.current_line_number] = node.linestart
        return super(LineMapWalker, self).default(node)

    def n_LOAD_CONST(self, node):
        if hasattr(node, 'linestart'):
            if node.linestart:
                self.source_linemap[self.current_line_number] = node.linestart
        return super(LineMapWalker, self).n_LOAD_CONST(node)


class LineMapFragmentWalker(fragments.FragmentsWalker, LineMapWalker):
    def __init__(self, *args, **kwargs):
        super(LineMapFragmentWalker, self).__init__(*args, **kwargs)
        self.source_linemap = {}
        self.current_line_number = 0

def deparse_code_with_map(*args, **kwargs):
    """
    Like deparse_code but saves line number correspondences.
    Deprecated. Use code_deparse_with_map
    """
    kwargs['walker'] = LineMapWalker
    return code_deparse(*args, **kwargs)

def code_deparse_with_map(*args, **kwargs):
    """
    Like code_deparse but saves line number correspondences.
    """
    kwargs['walker'] = LineMapWalker
    return code_deparse(*args, **kwargs)

def deparse_code_with_fragments_and_map(*args, **kwargs):
    """
    Like deparse_code_with_map but saves fragments.
    Deprecated. Use code_deparse_with_fragments_and_map
    """
    kwargs['walker'] = LineMapFragmentWalker
    return fragments.deparse_code(*args, **kwargs)

def code_deparse_with_fragments_and_map(*args, **kwargs):
    """
    Like code_deparse_with_map but saves fragments.
    """
    kwargs['walker'] = LineMapFragmentWalker
    return fragments.code_deparse(*args, **kwargs)

if __name__ == '__main__':
    def deparse_test(co):
        "This is a docstring"
        deparsed = code_deparse_with_map(co)
        a = 1; b = 2
        print("\n")
        linemap = [(line_no, deparsed.source_linemap[line_no])
                       for line_no in
                       sorted(deparsed.source_linemap.keys())]
        print(linemap)
        deparsed = code_deparse_with_fragments_and_map(co)
        print("\n")
        linemap2 = [(line_no, deparsed.source_linemap[line_no])
                   for line_no in
                   sorted(deparsed.source_linemap.keys())]
        print(linemap2)
        # assert linemap == linemap2
        return
    deparse_test(deparse_test.__code__)
