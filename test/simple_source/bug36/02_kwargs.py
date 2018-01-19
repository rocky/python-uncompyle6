# From 3.6 _markupbase _parse_doctype_subset()
def bug(self, j):
    self.parse_comment(j, report=0)
    self.parse_comment(j, report=1, foo=2)
    self.parse_comment(a, b, report=3)
