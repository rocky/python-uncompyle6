#  Copyright (c) 2018 by Rocky Bernstein
from uncompyle6.semantics.pysource import SourceWalker, deparse_code
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
    """
    kwargs['walker'] = LineMapWalker
    return deparse_code(*args, **kwargs)

def deparse_code_with_fragments_and_map(*args, **kwargs):
    """
    Like deparse_code_with_map but saves fragments.
    """
    kwargs['walker'] = LineMapFragmentWalker
    return fragments.deparse_code(*args, **kwargs)

if __name__ == '__main__':
    def deparse_test(co):
        "This is a docstring"
        import sys
        sys_version = float(sys.version[0:3])
        # deparsed = deparse_code(sys_version, co, showasm=True, showast=True)
        deparsed = deparse_code_with_map(sys_version, co, showasm=False,
                                         showast=False,
                                         showgrammar=False)
        a = 1; b = 2
        print("\n")
        linemap = [(line_no, deparsed.source_linemap[line_no])
                       for line_no in
                       sorted(deparsed.source_linemap.keys())]
        print(linemap)
        deparsed = deparse_code_with_fragments_and_map(sys_version,
                                                       co, showasm=False,
                                                       showast=False,
                                                       showgrammar=False)
        a = 1; b = 2
        print("\n")
        linemap2 = [(line_no, deparsed.source_linemap[line_no])
                   for line_no in
                   sorted(deparsed.source_linemap.keys())]
        print(linemap2)
        assert linemap == linemap2
        return
    deparse_test(deparse_test.__code__)
