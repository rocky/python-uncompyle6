"""
CPython magic- and version- independent marshal routines

This is needed when the bytecode extracted is from
a different version than the currently-running Python.

When the two are the same, you can simply use Python's built-in marshal.loads()
to produce a code object
"""

# Copyright (c) 1999 John Aycock
# Copyright (c) 2000-2002 by hartmut Goebel <h.goebel@crazy-compilers.com>
# Copyright (c) 2005 by Dan Pascu <dan@windowmaker.org>
# Copyright (c) 2015 by Rocky Bernstein

from __future__ import print_function

import sys, types
from struct import unpack

from uncompyle6.magics import PYTHON_MAGIC_INT

internStrings = []

PYTHON3 = (sys.version_info >= (3, 0))

if PYTHON3:
    def long(n): return n

def compat_str(s):
    return s.decode('utf-8', errors='ignore') if PYTHON3 else str(s)

def load_code(fp, magic_int):
    """
    marshal.load() written in Python. When the Python bytecode magic loaded is the
    same magic for the running Python interpreter, we can simply use the
    Python-supplied mashal.load().

    However we need to use this when versions are different since the internal
    code structures are different. Sigh.
    """
    global internStrings
    internStrings = []
    seek_pos = fp.tell()
    # Do a sanity check. Is this a code type?
    if fp.read(1).decode('utf-8') != 'c':
        raise TypeError("File %s doesn't smell like Python bytecode" % fp.name)

    fp.seek(seek_pos)
    return load_code_internal(fp, magic_int)

def load_code_internal(fp, magic_int, bytes_for_s=False):
    global internStrings

    b1 = fp.read(1)
    marshalType = b1.decode('utf-8')
    if marshalType == 'c':
        Code = types.CodeType

        # FIXME If 'i' is deprecated, what would we use?
        co_argcount = unpack('i', fp.read(4))[0]
        co_nlocals = unpack('i', fp.read(4))[0]
        co_stacksize = unpack('i', fp.read(4))[0]
        co_flags = unpack('i', fp.read(4))[0]
        # FIXME: somewhere between Python 2.7 and python 3.2 there's
        # another 4 bytes before we get to the bytecode. What's going on?
        # Again, because magic ints decreased between python 2.7 and 3.0 we need
        # a range here.
        if 3000 < magic_int < 20121:
            fp.read(4)

        co_code = load_code_internal(fp, magic_int, bytes_for_s=True)
        co_consts = load_code_internal(fp, magic_int)
        co_names = load_code_internal(fp, magic_int)
        co_varnames = load_code_internal(fp, magic_int)
        co_freevars = load_code_internal(fp, magic_int)
        co_cellvars = load_code_internal(fp, magic_int)
        co_filename = load_code_internal(fp, magic_int)
        co_name = load_code_internal(fp, magic_int)
        co_firstlineno = unpack('i', fp.read(4))[0]
        co_lnotab = load_code_internal(fp, magic_int)
        # The Python3 code object is different than Python2's which
        # we are reading if we get here.
        # Also various parameters which were strings are now
            # bytes (which is probably more logical).
        if PYTHON3:
            if PYTHON_MAGIC_INT > 3020:
                # In later Python3 magic_ints, there is a
                # kwonlyargcount parameter which we set to 0.
                return Code(co_argcount, 0, co_nlocals, co_stacksize, co_flags,
                            co_code,
                            co_consts, co_names, co_varnames, co_filename, co_name,
                            co_firstlineno, bytes(co_lnotab, encoding='utf-8'),
                            co_freevars, co_cellvars)
            else:
                return Code(co_argcount, 0, co_nlocals, co_stacksize, co_flags,
                            co_code,
                            co_consts, co_names, co_varnames, co_filename, co_name,
                            co_firstlineno, bytes(co_lnotab, encoding='utf-8'),
                            co_freevars, co_cellvars)
        else:
            if (3000 < magic_int < 20121):
                # Python 3  encodes some fields as Unicode while Python2
                # requires the corresponding field to have string values
                co_consts = tuple([str(s) if s else None for s in co_consts])
                co_names  = tuple([str(s) if s else None for s in co_names])
                co_varnames  = tuple([str(s) if s else None for s in co_varnames])
                co_filename = str(co_filename)
                co_name = str(co_name)
            return Code(co_argcount, co_nlocals, co_stacksize, co_flags, co_code,
                        co_consts, co_names, co_varnames, co_filename, co_name,
                        co_firstlineno, co_lnotab, co_freevars, co_cellvars)

    # const type
    elif marshalType == '.':
        return Ellipsis
    elif marshalType == '0':
        raise KeyError(marshalType)
        return None
    elif marshalType == 'N':
        return None
    elif marshalType == 'T':
        return True
    elif marshalType == 'F':
        return False
    elif marshalType == 'S':
        return StopIteration
    # number type
    elif marshalType == 'f':
        n = fp.read(1)
        return float(unpack('d', fp.read(n))[0])
    elif marshalType == 'g':
        return float(unpack('d', fp.read(8))[0])
    elif marshalType == 'i':
        return int(unpack('i', fp.read(4))[0])
    elif marshalType == 'I':
        return unpack('q', fp.read(8))[0]
    elif marshalType == 'x':
        raise KeyError(marshalType)
        return None
    elif marshalType == 'y':
        raise KeyError(marshalType)
        return None
    elif marshalType == 'l':
        n = unpack('i', fp.read(4))[0]
        if n == 0:
            return long(0)
        size = abs(n)
        d = long(0)
        for j in range(0, size):
            md = int(unpack('h', fp.read(2))[0])
            d += md << j*15
        if n < 0:
            return long(d*-1)
        return d
    # strings type
    elif marshalType == 'R':
        refnum = unpack('i', fp.read(4))[0]
        return internStrings[refnum]
    elif marshalType == 's':
        strsize = unpack('i', fp.read(4))[0]
        s = fp.read(strsize)
        if not bytes_for_s:
            s = compat_str(s)
        return s
    elif marshalType == 't':
        strsize = unpack('i', fp.read(4))[0]
        interned = compat_str(fp.read(strsize))
        internStrings.append(interned)
        return interned
    elif marshalType == 'u':
        strsize = unpack('i', fp.read(4))[0]
        unicodestring = fp.read(strsize)
        return unicodestring.decode('utf-8')
    # collection type
    elif marshalType == '(':
        tuplesize = unpack('i', fp.read(4))[0]
        ret = tuple()
        while tuplesize > 0:
            ret += load_code_internal(fp, magic_int),
            tuplesize -= 1
        return ret
    elif marshalType == '[':
        raise KeyError(marshalType)
        return None
    elif marshalType == '{':
        raise KeyError(marshalType)
        return None
    elif marshalType in ['<', '>']:
        raise KeyError(marshalType)
        return None
    else:
        sys.stderr.write("Unknown type %i (hex %x)\n" % (ord(marshalType), ord(marshalType)))
    return
