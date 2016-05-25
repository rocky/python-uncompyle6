import sys
from uncompyle6 import PYTHON3
from uncompyle6.scanners.tok import NoneToken

if PYTHON3:
    intern = sys.intern
    from collections import UserList
else:
    from UserList import UserList

indent_symbols = ['\xb7','|','*','+',':','!']
current_indsym = indent_symbols[:]

class AST(UserList):
    def __init__(self, kind, kids=[]):
        self.type = intern(kind)
        UserList.__init__(self, kids)

    def isNone(self):
        """An AST None token. We can't use regular list comparisons
        because AST token offsets might be different"""
        return len(self.data) == 1 and NoneToken == self.data[0]

    def __getslice__(self, low, high):
        return self.data[low:high]

    def __eq__(self, o):
        if isinstance(o, AST):
            return self.type == o.type \
                   and UserList.__eq__(self, o)
        else:
            return self.type == o

    def __hash__(self):
        return hash(self.type)

    def __repr__(self, indent=''):
        global current_indsym
        rv = str(self.type)
        if not current_indsym:
            current_indsym = indent_symbols[:]
        indsym = current_indsym.pop(0)
        for k in self:
            rv = rv + '\n' + str(k).lstrip(' \t').replace('\n', '\n%s   ' % indsym)
        return rv
