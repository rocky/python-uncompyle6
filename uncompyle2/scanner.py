#  Copyright (c) 1999 John Aycock
#  Copyright (c) 2000-2002 by hartmut Goebel <h.goebel@crazy-compilers.com>
#  Copyright (c) 2005 by Dan Pascu <dan@windowmaker.org>
#
#  See main module for license.
#

__all__ = ['Token', 'Scanner', 'Code']

import types
from collections import namedtuple
from array import array
from operator import itemgetter

from uncompyle2.opcode import opcode_25, opcode_26, opcode_27

class Token:
    '''
    Class representing a byte-code token.
    
    A byte-code token is equivalent to the contents of one line
    as output by dis.dis().
    '''
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
    '''
    Class for representing code-objects.

    This is similar to the original code object, but additionally
    the diassembled code is stored in the attribute '_tokens'.
    '''
    def __init__(self, co, scanner, classname=None):
        for i in dir(co):
            if i.startswith('co_'):
                setattr(self, i, getattr(co, i))
        self._tokens, self._customize = scanner.disassemble(co, classname)

class Scanner(object):
    opc = None # opcode module

    def __init__(self, version):
        if version == 2.7:
            self.opc = opcode_27
        elif version == 2.6:
            self.opc = opcode_26
        elif version == 2.5:
            self.opc = opcode_25
        
        return self.resetTokenClass()
    
    def setShowAsm(self, showasm, out=None):
        self.showasm = showasm
        self.out = out
        
    def setTokenClass(self, tokenClass):
        assert type(tokenClass) == types.ClassType
        self.Token = tokenClass
        return self.Token
        
    def resetTokenClass(self):
        return self.setTokenClass(Token)
        
    def get_target(self, pos, op=None):
        if op is None:
            op = self.code[pos]
        target = self.get_argument(pos)
        if op in self.opc.hasjrel:
            target += pos + 3
        return target

    def get_argument(self, pos):
        arg = self.code[pos+1] + self.code[pos+2] * 256
        return arg

    def print_bytecode(self):
        for i in self.op_range(0, len(self.code)):
            op = self.code[i]
            if op in self.opc.hasjabs+self.opc.hasjrel:
                dest = self.get_target(i, op)
                print '%i\t%s\t%i' % (i, self.opc.opname[op], dest)
            else:
                print '%i\t%s\t' % (i, self.opc.opname[op])
        
    def first_instr(self, start, end, instr, target=None, exact=True):
        '''
        Find the first <instr> in the block from start to end.
        <instr> is any python bytecode instruction or a list of opcodes
        If <instr> is an opcode with a target (like a jump), a target
        destination can be specified which must match precisely if exact
        is True, or if exact is False, the instruction which has a target
        closest to <target> will be returned.

        Return index to it or None if not found.
        '''
        code = self.code
        assert(start>=0 and end<=len(code))

        try:    None in instr
        except: instr = [instr]

        pos = None
        distance = len(code)
        for i in self.op_range(start, end):
            op = code[i]
            if op in instr:
                if target is None:
                    return i
                dest = self.get_target(i, op)
                if dest == target:
                    return i
                elif not exact:
                    _distance = abs(target - dest)
                    if _distance < distance:
                        distance = _distance
                        pos = i
        return pos

    def last_instr(self, start, end, instr, target=None, exact=True):
        '''
        Find the last <instr> in the block from start to end.
        <instr> is any python bytecode instruction or a list of opcodes
        If <instr> is an opcode with a target (like a jump), a target
        destination can be specified which must match precisely if exact
        is True, or if exact is False, the instruction which has a target
        closest to <target> will be returned.

        Return index to it or None if not found.
        '''

        code = self.code
        if not (start>=0 and end<=len(code)):
            return None

        try:    None in instr
        except: instr = [instr]

        pos = None
        distance = len(code)
        for i in self.op_range(start, end):
            op = code[i]
            if op in instr:
                if target is None:
                    pos = i
                else:
                    dest = self.get_target(i, op)
                    if dest == target:
                        distance = 0
                        pos = i
                    elif not exact:
                        _distance = abs(target - dest)
                        if _distance <= distance:
                            distance = _distance
                            pos = i
        return pos

    def all_instr(self, start, end, instr, target=None, include_beyond_target=False):
        '''
        Find all <instr> in the block from start to end.
        <instr> is any python bytecode instruction or a list of opcodes
        If <instr> is an opcode with a target (like a jump), a target
        destination can be specified which must match precisely.

        Return a list with indexes to them or [] if none found.
        '''
        
        code = self.code
        assert(start>=0 and end<=len(code))

        try:    None in instr
        except: instr = [instr]

        result = []
        for i in self.op_range(start, end):
            op = code[i]
            if op in instr:
                if target is None:
                    result.append(i)
                else:
                    t = self.get_target(i, op)
                    if include_beyond_target and t >= target:
                        result.append(i)
                    elif t == target:
                        result.append(i)
        return result
    
    def op_size(self, op):
        if op < self.opc.HAVE_ARGUMENT and op not in self.opc.hasArgumentExtended:
            return 1
        else:
            return 3
    
    def op_hasArgument(self, op):
        return self.op_size(op) > 1
    
    def op_range(self, start, end):
        while start < end:
            yield start
            start += self.op_size(self.code[start])
            
    def remove_mid_line_ifs(self, ifs):
        filtered = []
        for i in ifs:
            if self.lines[i].l_no == self.lines[i+3].l_no:
                if self.code[self.prev[self.lines[i].next]] in (self.opc.PJIT, self.opc.PJIF):
                    continue
            filtered.append(i)
        return filtered
    
    def rem_or(self, start, end, instr, target=None, include_beyond_target=False):
        '''
        Find all <instr> in the block from start to end.
        <instr> is any python bytecode instruction or a list of opcodes
        If <instr> is an opcode with a target (like a jump), a target
        destination can be specified which must match precisely.

        Return a list with indexes to them or [] if none found.
        '''
        
        code = self.code
        assert(start>=0 and end<=len(code))

        try:    None in instr
        except: instr = [instr]

        result = []
        for i in self.op_range(start, end):
            op = code[i]
            if op in instr:
                if target is None:
                    result.append(i)
                else:
                    t = self.get_target(i, op)
                    if include_beyond_target and t >= target:
                        result.append(i)
                    elif t == target:
                        result.append(i)
                        
        pjits = self.all_instr(start, end, self.opc.PJIT)
        filtered = []
        for pjit in pjits:
            tgt = self.get_target(pjit)-3
            for i in result:
                if i <= pjit or i >= tgt:
                    filtered.append(i)
            result = filtered
            filtered = []
        return result

    def restrict_to_parent(self, target, parent):
        '''Restrict pos to parent boundaries.'''
        if not (parent['start'] < target < parent['end']):
            target = parent['end']
        return target