#  Copyright (c) 2016 by Rocky Bernstein
#  Copyright (c) 2000-2002 by hartmut Goebel <h.goebel@crazy-compilers.com>
#  Copyright (c) 1999 John Aycock

import sys
from uncompyle6 import PYTHON3

if PYTHON3:
    intern = sys.intern

class Token:
    """
    Class representing a byte-code instruction.

    A byte-code token is equivalent to Python 3's dis.instruction or
    the contents of one line as output by dis.dis().
    """
    # FIXME: match Python 3.4's terms:
    #    type_ should be opname
    #    linestart = starts_line
    #    attr = argval
    #    pattr = argrepr
    def __init__(self, type_, attr=None, pattr=None, offset=-1, linestart=None):
        self.type = intern(type_)
        self.attr = attr
        self.pattr = pattr
        self.offset = offset
        self.linestart = linestart

    def __eq__(self, o):
        """ '==', but it's okay if offsets and linestarts are different"""
        if isinstance(o, Token):
            # Both are tokens: compare type and attr
            # It's okay if offsets are different
            return (self.type == o.type) and (self.pattr == o.pattr)
        else:
            return self.type == o

    def __repr__(self):
        return str(self.type)

    def __str__(self):
        pattr = self.pattr if self.pattr is not None else ''
        prefix = '\n%4d  ' % self.linestart if self.linestart else (' ' * 6)
        return (prefix +
                ('%6s\t%-17s %r' % (self.offset, self.type, pattr)))

    def format(self):
        prefix = '\n%4d ' % self.linestart if self.linestart else (' ' * 5)
        offset_opname = '%6s\t%-17s' % (self.offset, self.type)
        argstr = "%6d " % self.attr if isinstance(self.attr, int) else (' '*7)
        pattr = self.pattr if self.pattr is not None else ''
        return "%s%s%s %r" % (prefix, offset_opname,  argstr, pattr)

    def __hash__(self):
        return hash(self.type)

    def __getitem__(self, i):
        raise IndexError

NoneToken = Token('LOAD_CONST', offset=-1, attr=None, pattr=None)
