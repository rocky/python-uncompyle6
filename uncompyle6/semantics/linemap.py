from uncompyle6.semantics.pysource import SourceWalker, deparse_code

# FIXME: does this handle nested code, and lambda properly
class LineMapWalker(SourceWalker):
<<<<<<< HEAD
    def __init__(self, *args, **kwargs):
        if 'first_line' not in kwargs:
            first_line = 0
=======
    def __init__(self, *args, first_line=0, **kwargs):
>>>>>>> Forgot to add linemap file
        super(LineMapWalker, self).__init__(*args, **kwargs)
        self.source_linemap = {}
        self.current_line_number = first_line

    def write(self, *data):
        """Augment write routine to keep track of current line"""
        for l in data:
            for i in str(l):
                if i == '\n':
                    self.current_line_number += 1
                    pass
                pass
            pass
        return super(LineMapWalker, self).write(*data)

    def default(self, node):
        """Augment write default routine to record line number changes"""
        if hasattr(node, 'linestart'):
            if node.linestart:
                self.source_linemap[self.current_line_number] = node.linestart
        return super(LineMapWalker, self).default(node)

def deparse_code_with_map(*args, first_line=0, **kwargs):
    """
    Like deparse_code but saves line number correspondences.
    """
    kwargs['walker'] = LineMapWalker
    return deparse_code(*args, **kwargs)

if __name__ == '__main__':
    def deparse_test(co):
        "This is a docstring"
        import sys
        sys_version = float(sys.version[0:3])
        # deparsed = deparse_code(sys_version, co, showasm=True, showast=True)
        deparsed = deparse_code_with_map(sys_version, co, showasm=False, showast=False,
                                         showgrammar=False)
        a = 1; b = 2
        print("\n")
        linemap = [(line_no, deparsed.source_linemap[line_no])
                       for line_no in
                       sorted(deparsed.source_linemap.keys())]
        print(linemap)
        return
    deparse_test(deparse_test.__code__)
