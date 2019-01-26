#  Copyright (c) 2016-2018 by Rocky Bernstein
#  Copyright (c) 2000-2002 by hartmut Goebel <h.goebel@crazy-compilers.com>
#  Copyright (c) 1999 John Aycock
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

import re, sys
from uncompyle6 import PYTHON3

if PYTHON3:
    intern = sys.intern

class Token:   # Python 2.4 can't have empty ()
    """
    Class representing a byte-code instruction.

    A byte-code token is equivalent to Python 3's dis.instruction or
    the contents of one line as output by dis.dis().
    """
    # FIXME: match Python 3.4's terms:
    #    linestart = starts_line
    #    attr = argval
    #    pattr = argrepr
    def __init__(self, opname, attr=None, pattr=None, offset=-1,
                 linestart=None, op=None, has_arg=None, opc=None):
        self.kind = intern(opname)
        self.has_arg = has_arg
        self.attr = attr
        self.pattr = pattr
        self.offset = offset
        self.linestart = linestart
        if has_arg is False:
            self.attr = None
            self.pattr = None

        if opc is None:
            from xdis.std import _std_api
            self.opc = _std_api.opc
        else:
            self.opc = opc
        if op is None:
            self.op = self.opc.opmap.get(self.kind, None)
        else:
            self.op = op

    def __eq__(self, o):
        """ '==' on kind and "pattr" attributes.
            It is okay if offsets and linestarts are different"""
        if isinstance(o, Token):
            return (self.kind == o.kind) and (self.pattr == o.pattr)
        else:
            # ?? do we need this?
            return self.kind == o

    def __ne__(self, o):
        """ '!=', but it's okay if offsets and linestarts are different"""
        return not self.__eq__(o)

    def __repr__(self):
        return str(self.kind)

    # def __str__(self):
    #     pattr = self.pattr if self.pattr is not None else ''
    #     prefix = '\n%3d   ' % self.linestart if self.linestart else (' ' * 6)
    #     return (prefix +
    #             ('%9s  %-18s %r' % (self.offset, self.kind, pattr)))

    def __str__(self):
        return self.format(line_prefix='')

    def format(self, line_prefix=''):
        if self.linestart:
            prefix = '\n%s%4d  ' % (line_prefix, self.linestart)
        else:
            prefix = ' ' * (6 + len(line_prefix))
        offset_opname = '%6s  %-17s' % (self.offset, self.kind)
        if not self.has_arg:
            return "%s%s" % (prefix, offset_opname)

        if isinstance(self.attr, int):
            argstr = "%6d " % self.attr
        else:
            argstr = ' '*7
        if self.has_arg:
            pattr = self.pattr
            if self.opc:
                if self.op in self.opc.JREL_OPS:
                    if not self.pattr.startswith('to '):
                        pattr = "to " + self.pattr
                elif self.op in self.opc.JABS_OPS:
                    self.pattr= str(self.pattr)
                    if not self.pattr.startswith('to '):
                        pattr = "to " + str(self.pattr)
                    pass
                elif self.op in self.opc.CONST_OPS:
                    # Compare with pysource n_LOAD_CONST
                    attr = self.attr
                    if attr is None:
                        pattr = None
                elif self.op in self.opc.hascompare:
                    if isinstance(self.attr, int):
                        pattr = self.opc.cmp_op[self.attr]
                # And so on. See xdis/bytecode.py get_instructions_bytes
                pass
        elif re.search(r'_\d+$', self.kind):
            return "%s%s%s" % (prefix, offset_opname,  argstr)
        else:
            pattr = ''
        return "%s%s%s %r" % (prefix, offset_opname,  argstr, pattr)

    def __hash__(self):
        return hash(self.kind)

    def __getitem__(self, i):
        raise IndexError

NoneToken = Token('LOAD_CONST', offset=-1, attr=None, pattr=None)
