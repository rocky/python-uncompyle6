#  Copyright (c) 1999 John Aycock
#  Copyright (c) 2000-2002 by hartmut Goebel <hartmut@goebel.noris.de>
#  Copyright (c) 2005 by Dan Pascu <dan@windowmaker.org>
#
#  See main module for license.
#

__all__ = ['Token', 'Scanner', 'getscanner']

import types
import disas as dis
from collections import namedtuple
from array import array
from operator import itemgetter

class Token:
    """
    Class representing a byte-code token.
    
    A byte-code token is equivalent to the contents of one line
    as output by dis.dis().
    """
    def __init__(self, type_, attr=None, pattr=None, offset=-1, linestart=False):
        self.type = intern(type_)
        self.attr = attr
        self.pattr = pattr
        self.offset = offset
        self.linestart = linestart
        
    def __cmp__(self, o):
        if isinstance(o, Token):
            # both are tokens: compare type and pattr 
            return cmp(self.type, o.type) or cmp(self.pattr, o.pattr)
        else:
            return cmp(self.type, o)

    def __repr__(self):		return str(self.type)
    def __str__(self):
        pattr = self.pattr
        if self.linestart:
            return '\n%s\t%-17s %r' % (self.offset, self.type, pattr)
        else:
            return '%s\t%-17s %r' % (self.offset, self.type, pattr)

    def __hash__(self):		return hash(self.type)
    def __getitem__(self, i):	raise IndexError


class Code:
    """
    Class for representing code-objects.

    This is similar to the original code object, but additionally
    the diassembled code is stored in the attribute '_tokens'.
    """
    def __init__(self, co, scanner, classname=None):
        for i in dir(co):
            if i.startswith('co_'):
                setattr(self, i, getattr(co, i))
        self._tokens, self._customize = scanner.disassemble(co, classname)
