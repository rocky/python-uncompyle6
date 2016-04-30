import sys
from uncompyle6 import PYTHON3
from uncompyle6.scanners.tok import NoneToken

if PYTHON3:
    intern = sys.intern
    from collections import UserList
else:
    from UserList import UserList


class AST(UserList):
    def __init__(self, kind, kids=[]):
        self.type = intern(kind)
        UserList.__init__(self, kids)

    def isNone(self):
        """An AST None token. We can't use regular list comparisons
        because AST token offsets might be different"""
        return len(self.data) == 1 and NoneToken == self.data[0]

    def __getslice__(self, low, high):    return self.data[low:high]

    def __eq__(self, o):
        if isinstance(o, AST):
            return self.type == o.type \
                   and UserList.__eq__(self, o)
        else:
            return self.type == o

    def __hash__(self):
        return hash(self.type)

    def __repr__(self, indent=''):
        rv = str(self.type)
        for k in self:
            rv = rv + '\n' + str(k).replace('\n', '\n   ')
        return rv
