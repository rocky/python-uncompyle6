import sys
from uncompyle6 import PYTHON3
if PYTHON3:
    from io import StringIO
    minint = -sys.maxsize-1
    maxint = sys.maxsize
else:
    from StringIO import StringIO
    minint = -sys.maxint-1
    maxint = sys.maxint
from uncompyle6.semantics.helper import print_docstring

class PrintFake():
    def __init__(self):
        self.pending_newlines = 0
        self.f = StringIO()

    def write(self, *data):
        if (len(data) == 0) or (len(data) == 1 and data[0] == ''):
            return
        out = ''.join((str(j) for j in data))
        n = 0
        for i in out:
            if i == '\n':
                n += 1
                if n == len(out):
                    self.pending_newlines = max(self.pending_newlines, n)
                    return
            elif n:
                self.pending_newlines = max(self.pending_newlines, n)
                out = out[n:]
                break
            else:
                break

        if self.pending_newlines > 0:
            self.f.write('\n'*self.pending_newlines)
            self.pending_newlines = 0

        for i in out[::-1]:
            if i == '\n':
                self.pending_newlines += 1
            else:
                break

        if self.pending_newlines:
            out = out[:-self.pending_newlines]
        self.f.write(out)
    def println(self, *data):
        if data and not(len(data) == 1 and data[0] ==''):
            self.write(*data)
        self.pending_newlines = max(self.pending_newlines, 1)
        return
    pass

def test_docstring():

    for doc, expect in (
            ("Now is the time",
             '  """Now is the time"""'),
           ("""
Now is the time
""",
            '''  """
  Now is the time
  """''')

            # (r'''func placeholder - ' and with ("""\nstring\n  """)''',
            #  """  r'''func placeholder - ' and with (\"\"\"\nstring\n\"\"\")'''"""),
            # (r"""func placeholder - ' and with ('''\nstring\n''') and \"\"\"\nstring\n\"\"\" """,
            # """  r\"\"\"func placeholder - ' and with ('''\nstring\n''') and \"\"\"\nstring\n\"\"\" \"\"\"""")
            ):

        o = PrintFake()
        # print(doc)
        # print(expect)
        print_docstring(o, '  ', doc)
        assert expect == o.f.getvalue()
