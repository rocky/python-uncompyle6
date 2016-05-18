#
# (C) Copyright 2000-2002 by hartmut Goebel <h.goebel@crazy-compilers.com>
# (C) Copyright 2015 by Rocky Bernstein
#
"""
byte-code verification
"""

from __future__ import print_function

import dis, inspect, operator

import uncompyle6
import uncompyle6.scanner as scanner
from uncompyle6 import PYTHON3
from uncompyle6.code import iscode
from uncompyle6.magics import PYTHON_MAGIC_INT
from uncompyle6.load import load_file, load_module

# FIXME: DRY
if PYTHON3:
    truediv = operator.truediv
    from functools import reduce
else:
    truediv = operator.div


def code_equal(a, b):
    return a.co_code == b.co_code

BIN_OP_FUNCS = {
'BINARY_POWER': operator.pow,
'BINARY_MULTIPLY': operator.mul,
'BINARY_DIVIDE': truediv,
'BINARY_FLOOR_DIVIDE': operator.floordiv,
'BINARY_TRUE_DIVIDE': operator.truediv,
'BINARY_MODULO' : operator.mod,
'BINARY_ADD': operator.add,
'BINARY_SUBRACT': operator.sub,
'BINARY_LSHIFT': operator.lshift,
'BINARY_RSHIFT': operator.rshift,
'BINARY_AND': operator.and_,
'BINARY_XOR': operator.xor,
'BINARY_OR': operator.or_,
}

JUMP_OPs = None

# --- exceptions ---

class VerifyCmpError(Exception):
    pass

class CmpErrorConsts(VerifyCmpError):
    """Exception to be raised when consts differ."""
    def __init__(self, name, index):
        self.name = name
        self.index = index

    def __str__(self):
        return 'Compare Error within Consts of %s at index %i' % \
               (repr(self.name), self.index)

class CmpErrorConstsType(VerifyCmpError):
    """Exception to be raised when consts differ."""
    def __init__(self, name, index):
        self.name = name
        self.index = index

    def __str__(self):
        return 'Consts type differ in %s at index %i' % \
               (repr(self.name), self.index)

class CmpErrorConstsLen(VerifyCmpError):
    """Exception to be raised when length of co_consts differs."""
    def __init__(self, name, consts1, consts2):
        self.name = name
        self.consts = (consts1, consts2)

    def __str__(self):
        return 'Consts length differs in %s:\n\n%i:\t%s\n\n%i:\t%s\n\n' % \
               (repr(self.name),
            len(self.consts[0]), repr(self.consts[0]),
            len(self.consts[1]), repr(self.consts[1]))

class CmpErrorCode(VerifyCmpError):
    """Exception to be raised when code differs."""
    def __init__(self, name, index, token1, token2, tokens1, tokens2):
        self.name = name
        self.index = index
        self.token1 = token1
        self.token2 = token2
        self.tokens = [tokens1, tokens2]

    def __str__(self):
        s =  reduce(lambda s, t: "%s%-37s\t%-37s\n" % (s, t[0], t[1]),
                    list(map(lambda a, b: (a, b),
                             self.tokens[0],
                             self.tokens[1])),
                  'Code differs in %s\n' % str(self.name))
        return ('Code differs in %s at offset %s [%s] != [%s]\n\n' %
                (repr(self.name), self.index,
                 repr(self.token1), repr(self.token2))) + s

class CmpErrorCodeLen(VerifyCmpError):
    """Exception to be raised when code length differs."""
    def __init__(self, name, tokens1, tokens2):
        self.name = name
        self.tokens = [tokens1, tokens2]

    def __str__(self):
        return reduce(lambda s, t: "%s%-37s\t%-37s\n" % (s, t[0], t[1]),
                      list(map(lambda a, b: (a, b),
                               self.tokens[0],
                               self.tokens[1])),
                  'Code len differs in %s\n' % str(self.name))

class CmpErrorMember(VerifyCmpError):
    """Exception to be raised when other members differ."""
    def __init__(self, name, member, data1, data2):
        self.name = name
        self.member = member
        self.data = (data1, data2)

    def __str__(self):
        return 'Member %s differs in %s:\n\t%s\n\t%s\n' % \
               (repr(self.member), repr(self.name),
            repr(self.data[0]), repr(self.data[1]))

# --- compare ---

# these members are ignored
__IGNORE_CODE_MEMBERS__ = ['co_filename', 'co_firstlineno', 'co_lnotab', 'co_stacksize', 'co_names']

def cmp_code_objects(version, code_obj1, code_obj2, name=''):
    """
    Compare two code-objects.

    This is the main part of this module.
    """
    # print code_obj1, type(code_obj2)
    assert iscode(code_obj1), \
      "cmp_code_object first object type is %s, not code" % type(code_obj1)
    assert iscode(code_obj2), \
      "cmp_code_object second object type is %s, not code" % type(code_obj2)
    # print dir(code_obj1)
    if isinstance(code_obj1, object):
        # new style classes (Python 2.2)
        # assume _both_ code objects to be new stle classes
        assert dir(code_obj1) == dir(code_obj2)
    else:
        # old style classes
        assert dir(code_obj1) == code_obj1.__members__
        assert dir(code_obj2) == code_obj2.__members__
        assert code_obj1.__members__ == code_obj2.__members__

    if name == '__main__':
        name = code_obj1.co_name
    else:
        name = '%s.%s' % (name, code_obj1.co_name)
        if name == '.?': name = '__main__'

    if isinstance(code_obj1, object) and code_equal(code_obj1, code_obj2):
        # use the new style code-classes' __cmp__ method, which
        # should be faster and more sophisticated
        # if this compare fails, we use the old routine to
        # find out, what exactly is nor equal
        # if this compare succeds, simply return
        # return
        pass

    if isinstance(code_obj1, object):
        members = [x for x in dir(code_obj1) if x.startswith('co_')]
    else:
        members = dir(code_obj1)
    members.sort()  # ; members.reverse()

    tokens1 = None
    for member in members:
        if member in __IGNORE_CODE_MEMBERS__:
            pass
        elif member == 'co_code':
            if version == 2.5:
                import uncompyle6.scanners.scanner25 as scan
                scanner = scan.Scanner25()
            elif version == 2.6:
                import uncompyle6.scanners.scanner26 as scan
                scanner = scan.Scanner26()
            elif version == 2.7:
                import uncompyle6.scanners.scanner27 as scan
                scanner = scan.Scanner27()
            elif version == 3.2:
                import uncompyle6.scanners.scanner32 as scan
                scanner = scan.Scanner32()
            elif version == 3.3:
                import uncompyle6.scanners.scanner33 as scan
                scanner = scan.Scanner33()
            elif version == 3.4:
                import uncompyle6.scanners.scanner34 as scan
                scanner = scan.Scanner34()
            elif version == 3.5:
                import uncompyle6.scanners.scanner35 as scan
                scanner = scan.Scanner35()

            global JUMP_OPs
            JUMP_OPs = list(scan.JUMP_OPs) + ['JUMP_BACK']

            # use changed Token class
            #   We (re)set this here to save exception handling,
            #   which would get confusing.
            scanner.setTokenClass(Token)
            try:
                # disassemble both code-objects
                tokens1, customize = scanner.disassemble(code_obj1)
                del customize # save memory
                tokens2, customize = scanner.disassemble(code_obj2)
                del customize # save memory
            finally:
                scanner.resetTokenClass() # restore Token class

            targets1 = dis.findlabels(code_obj1.co_code)
            tokens1 = [t for t in tokens1 if t.type != 'COME_FROM']
            tokens2 = [t for t in tokens2 if t.type != 'COME_FROM']

            i1 = 0; i2 = 0
            offset_map = {}; check_jumps = {}
            while i1 < len(tokens1):
                if i2 >= len(tokens2):
                    if len(tokens1) == len(tokens2) + 2 \
                          and tokens1[-1].type == 'RETURN_VALUE' \
                          and tokens1[-2].type == 'LOAD_CONST' \
                          and tokens1[-2].pattr is None \
                          and tokens1[-3].type == 'RETURN_VALUE':
                        break
                    else:
                        raise CmpErrorCodeLen(name, tokens1, tokens2)

                offset_map[tokens1[i1].offset] = tokens2[i2].offset

                for idx1, idx2, offset2 in check_jumps.get(tokens1[i1].offset, []):
                    if offset2 != tokens2[i2].offset:
                        raise CmpErrorCode(name, tokens1[idx1].offset, tokens1[idx1],
                                   tokens2[idx2], tokens1, tokens2)

                if tokens1[i1].type != tokens2[i2].type:
                    if tokens1[i1].type == 'LOAD_CONST' == tokens2[i2].type:
                        i = 1
                        while tokens1[i1+i].type == 'LOAD_CONST':
                            i += 1
                        if tokens1[i1+i].type.startswith(('BUILD_TUPLE', 'BUILD_LIST')) \
                              and i == int(tokens1[i1+i].type.split('_')[-1]):
                            t = tuple([ elem.pattr for elem in tokens1[i1:i1+i] ])
                            if t != tokens2[i2].pattr:
                                raise CmpErrorCode(name, tokens1[i1].offset, tokens1[i1],
                                           tokens2[i2], tokens1, tokens2)
                            i1 += i + 1
                            i2 += 1
                            continue
                        elif i == 2 and tokens1[i1+i].type == 'ROT_TWO' and tokens2[i2+1].type == 'UNPACK_SEQUENCE_2':
                            i1 += 3
                            i2 += 2
                            continue
                        elif i == 2 and tokens1[i1+i].type in BIN_OP_FUNCS:
                            f = BIN_OP_FUNCS[tokens1[i1+i].type]
                            if f(tokens1[i1].pattr, tokens1[i1+1].pattr) == tokens2[i2].pattr:
                                i1 += 3
                                i2 += 1
                                continue
                    elif tokens1[i1].type == 'UNARY_NOT':
                        if tokens2[i2].type == 'POP_JUMP_IF_TRUE':
                            if tokens1[i1+1].type == 'POP_JUMP_IF_FALSE':
                                i1 += 2
                                i2 += 1
                                continue
                        elif tokens2[i2].type == 'POP_JUMP_IF_FALSE':
                            if tokens1[i1+1].type == 'POP_JUMP_IF_TRUE':
                                i1 += 2
                                i2 += 1
                                continue
                    elif tokens1[i1].type in ('JUMP_FORWARD', 'JUMP_BACK') \
                          and tokens1[i1-1].type == 'RETURN_VALUE' \
                          and tokens2[i2-1].type in ('RETURN_VALUE', 'RETURN_END_IF') \
                          and int(tokens1[i1].offset) not in targets1:
                        i1 += 1
                        continue
                    elif tokens1[i1].type == 'JUMP_FORWARD' and tokens2[i2].type == 'JUMP_BACK' \
                          and tokens1[i1+1].type == 'JUMP_BACK' and tokens2[i2+1].type == 'JUMP_BACK' \
                          and int(tokens1[i1].pattr) == int(tokens1[i1].offset) + 3:
                        if int(tokens1[i1].pattr) == int(tokens1[i1+1].offset):
                            i1 += 2
                            i2 += 2
                            continue

                    raise CmpErrorCode(name, tokens1[i1].offset, tokens1[i1],
                               tokens2[i2], tokens1, tokens2)
                elif tokens1[i1].type in JUMP_OPs and tokens1[i1].pattr != tokens2[i2].pattr:
                    dest1 = int(tokens1[i1].pattr)
                    dest2 = int(tokens2[i2].pattr)
                    if tokens1[i1].type == 'JUMP_BACK':
                        if offset_map[dest1] != dest2:
                            raise CmpErrorCode(name, tokens1[i1].offset, tokens1[i1],
                                       tokens2[i2], tokens1, tokens2)
                    else:
                        # import pdb; pdb.set_trace()
                        if dest1 in check_jumps:
                            check_jumps[dest1].append((i1, i2, dest2))
                        else:
                            check_jumps[dest1] = [(i1, i2, dest2)]

                i1 += 1
                i2 += 1
            del tokens1, tokens2 # save memory
        elif member == 'co_consts':
            # partial optimization can make the co_consts look different,
            #   so we'll just compare the code consts
            codes1 = ( c for c in code_obj1.co_consts if hasattr(c, 'co_consts') )
            codes2 = ( c for c in code_obj2.co_consts if hasattr(c, 'co_consts') )

            for c1, c2 in zip(codes1, codes2):
                cmp_code_objects(version, c1, c2, name=name)
        else:
            # all other members must be equal
            if getattr(code_obj1, member) != getattr(code_obj2, member):
                raise CmpErrorMember(name, member,
                             getattr(code_obj1, member),
                             getattr(code_obj2, member))

class Token(scanner.Token):
    """Token class with changed semantics for 'cmp()'."""

    def __cmp__(self, o):
        t = self.type # shortcut
        loads = ('LOAD_NAME', 'LOAD_GLOBAL', 'LOAD_CONST')
        if t in loads and o.type in loads:
            if self.pattr == 'None' and o.pattr is None:
                return 0
        if t == 'BUILD_TUPLE_0' and o.type == 'LOAD_CONST' and o.pattr == ():
            return 0
        if t == 'COME_FROM' == o.type:
            return 0
        if t == 'PRINT_ITEM_CONT' and o.type == 'PRINT_ITEM':
            return 0
        if t == 'RETURN_VALUE' and o.type == 'RETURN_END_IF':
            return 0
        if t == 'JUMP_IF_FALSE_OR_POP' and o.type == 'POP_JUMP_IF_FALSE':
            return 0
        if JUMP_OPs and t in JUMP_OPs:
            # ignore offset
            return t == o.type
        return (t ==  o.type) or self.pattr ==  o.pattr

    def __repr__(self):
        return '%s %s (%s)' % (str(self.type), str(self.attr),
                       repr(self.pattr))

    def __str__(self):
        return '%s\t%-17s %r' % (self.offset, self.type, self.pattr)

def compare_code_with_srcfile(pyc_filename, src_filename):
    """Compare a .pyc with a source code file."""
    version, timestamp, magic_int, code_obj1 = load_module(pyc_filename)
    if magic_int != PYTHON_MAGIC_INT:
        msg = ("Can't compare code - Python is running with magic %s, but code is magic %s "
               % (PYTHON_MAGIC_INT, magic_int))
        return msg
    code_obj2 = load_file(src_filename)
    cmp_code_objects(version, code_obj1, code_obj2)
    return None

def compare_files(pyc_filename1, pyc_filename2):
    """Compare two .pyc files."""
    version, timestamp, magic_int1, code_obj1 = uncompyle6.load_module(pyc_filename1)
    version, timestamp, magic_int2, code_obj2 = uncompyle6.load_module(pyc_filename2)
    cmp_code_objects(version, code_obj1, code_obj2)

if __name__ == '__main__':
    t1 = Token('LOAD_CONST', None, 'code_object _expandLang', 52)
    t2 = Token('LOAD_CONST', -421, 'code_object _expandLang', 55)
    print(repr(t1))
    print(repr(t2))
    print(t1.type ==  t2.type, t1.attr == t2.attr)
