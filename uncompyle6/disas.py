from __future__ import print_function

"""Disassembler of Python byte code into mnemonics.

This is needed when the bytecode extracted is from
a different version than the currently-running Python.

When the two are the same, you can simply use marshal.loads()
to prodoce a code object
"""

import marshal, pickle, sys, types

import dis as Mdis

from struct import unpack

internStrings = []

# XXX For backwards compatibility
disco = Mdis.disassemble

if (sys.version_info >= (3, 0)):
    def long(n):
        return n

def marshalLoad(fp):
    global internStrings
    internStrings = []
    return load(fp)

def load(fp):
    """
    Load marshal
    """
    global internStrings

    marshalType = fp.read(1).decode('utf-8')
    if marshalType == 'c':
        Code = types.CodeType

        co_argcount = unpack('i', fp.read(4))[0]
        co_nlocals = unpack('i', fp.read(4))[0]
        co_stacksize = unpack('i', fp.read(4))[0]
        co_flags = unpack('i', fp.read(4))[0]
        co_code = load(fp)
        co_consts = load(fp)
        co_names = load(fp)
        co_varnames = load(fp)
        co_freevars = load(fp)
        co_cellvars = load(fp)
        co_filename = load(fp)
        co_name = load(fp)
        co_firstlineno = unpack('i', fp.read(4))[0]
        co_lnotab = load(fp)
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
        return str(fp.read(strsize))
    elif marshalType == 't':
        strsize = unpack('i', fp.read(4))[0]
        interned = str(fp.read(strsize))
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
            ret += load(fp),
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

def _test():
    """Simple test program to disassemble a file."""
    if sys.argv[1:]:
        if sys.argv[2:]:
            sys.stderr.write("usage: python dis.py [-|file]\n")
            sys.exit(2)
        fn = sys.argv[1]
        if not fn or fn == "-":
            fn = None
    else:
        fn = None
    if fn is None:
        f = sys.stdin
    else:
        f = open(fn)
    source = f.read()
    if fn is not None:
        f.close()
    else:
        fn = "<stdin>"
    code = compile(source, fn, "exec")
    Mdis.dis(code)

if __name__ == "__main__":
    _test()
