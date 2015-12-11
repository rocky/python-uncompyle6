"""Disassembler of Python byte code into mnemonics."""

import sys
import types
from struct import unpack
import marshal, pickle

_have_code = (types.MethodType, types.FunctionType, types.CodeType, types.ClassType, type)
internStrings = []

def dis(x=None):
    """Disassemble classes, methods, functions, or code.
    With no argument, disassemble the last traceback.
    """
    if x is None:
        distb()
        return
    if isinstance(x, types.InstanceType):
        x = x.__class__
    if hasattr(x, 'im_func'):
        x = x.im_func
    if hasattr(x, 'func_code'):
        x = x.func_code
    if hasattr(x, '__dict__'):
        items = x.__dict__.items()
        items.sort()
        for name, x1 in items:
            if isinstance(x1, _have_code):
                print "Disassembly of %s:" % name
                try:
                    dis(x1)
                except TypeError, msg:
                    print "Sorry:", msg
                print
    elif hasattr(x, 'co_code'):
        disassemble(x)
    elif isinstance(x, str):
        disassemble_string(x)
    else:
        raise TypeError, \
              "don't know how to disassemble %s objects" % \
              type(x).__name__

def distb(tb=None):
    """Disassemble a traceback (default: last traceback)."""
    if tb is None:
        try:
            tb = sys.last_traceback
        except AttributeError:
            raise RuntimeError, "no last traceback to disassemble"
        while tb.tb_next: tb = tb.tb_next
    disassemble(tb.tb_frame.f_code, tb.tb_lasti)

def disassemble(co, lasti=-1):
    """Disassemble a code object."""
    code = co.co_code
    labels = findlabels(code)
    linestarts = dict(findlinestarts(co))
    n = len(code)
    i = 0
    extended_arg = 0
    free = None
    while i < n:
        c = code[i]
        op = ord(c)
        if i in linestarts:
            if i > 0:
                print
            print "%3d" % linestarts[i],
        else:
            print '   ',

        if i == lasti: print '-->',
        else: print '   ',
        if i in labels: print '>>',
        else: print '  ',
        print repr(i).rjust(4),
        print opname[op].ljust(20),
        i = i+1
        if op >= HAVE_ARGUMENT:
            oparg = ord(code[i]) + ord(code[i+1])*256 + extended_arg
            extended_arg = 0
            i = i+2
            if op == EXTENDED_ARG:
                extended_arg = oparg*65536L
            print repr(oparg).rjust(5),
            if op in hasconst:
                print '(' + repr(co.co_consts[oparg]) + ')',
            elif op in hasname:
                print '(' + co.co_names[oparg] + ')',
            elif op in hasjrel:
                print '(to ' + repr(i + oparg) + ')',
            elif op in haslocal:
                print '(' + co.co_varnames[oparg] + ')',
            elif op in hascompare:
                print '(' + cmp_op[oparg] + ')',
            elif op in hasfree:
                if free is None:
                    free = co.co_cellvars + co.co_freevars
                print '(' + free[oparg] + ')',
        print

def disassemble_string(code, lasti=-1, varnames=None, names=None,
                       constants=None):
    labels = findlabels(code)
    n = len(code)
    i = 0
    while i < n:
        c = code[i]
        op = ord(c)
        if i == lasti: print '-->',
        else: print '   ',
        if i in labels: print '>>',
        else: print '  ',
        print repr(i).rjust(4),
        print opname[op].ljust(15),
        i = i+1
        if op >= HAVE_ARGUMENT:
            oparg = ord(code[i]) + ord(code[i+1])*256
            i = i+2
            print repr(oparg).rjust(5),
            if op in hasconst:
                if constants:
                    print '(' + repr(constants[oparg]) + ')',
                else:
                    print '(%d)'%oparg,
            elif op in hasname:
                if names is not None:
                    print '(' + names[oparg] + ')',
                else:
                    print '(%d)'%oparg,
            elif op in hasjrel:
                print '(to ' + repr(i + oparg) + ')',
            elif op in haslocal:
                if varnames:
                    print '(' + varnames[oparg] + ')',
                else:
                    print '(%d)' % oparg,
            elif op in hascompare:
                print '(' + cmp_op[oparg] + ')',
        print

disco = disassemble 
# XXX For backwards compatibility

def findlabels(code):
    """Detect all offsets in a byte code which are jump targets.
    Return the list of offsets.
    """
    labels = []
    n = len(code)
    i = 0
    while i < n:
        c = code[i]
        op = ord(c)
        i = i+1
        if op >= HAVE_ARGUMENT:
            oparg = ord(code[i]) + ord(code[i+1])*256
            i = i+2
            label = -1
            if op in hasjrel:
                label = i+oparg
            elif op in hasjabs:
                label = oparg
            if label >= 0:
                if label not in labels:
                    labels.append(label)
    return labels

def findlinestarts(code):
    """Find the offsets in a byte code which are start of lines in the source.
    Generate pairs (offset, lineno) as described in Python/compile.c.
    """
    byte_increments = [ord(c) for c in code.co_lnotab[0::2]]
    line_increments = [ord(c) for c in code.co_lnotab[1::2]]

    lastlineno = None
    lineno = code.co_firstlineno
    addr = 0
    for byte_incr, line_incr in zip(byte_increments, line_increments):
        if byte_incr:
            if lineno != lastlineno:
                yield (addr, lineno)
                lastlineno = lineno
            addr += byte_incr
        lineno += line_incr
    if lineno != lastlineno:
        yield (addr, lineno)

def marshalLoad(fp):
    global internStrings
    internStrings = []
    return load(fp)
        
def load(fp):
    """
    Load marshal 
    """
    global internStrings
    
    marshalType = fp.read(1)
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
        return Code(co_argcount, co_nlocals, co_stacksize, co_flags, co_code, co_consts, co_names,\
        co_varnames, co_filename, co_name, co_firstlineno, co_lnotab, co_freevars, co_cellvars)
        
    # const type
    elif marshalType == '.':
        return Ellipsis 
    elif marshalType == '0':
        raise KeyError, marshalType
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
        raise KeyError, marshalType
        return None
    elif marshalType == 'y':
        raise KeyError, marshalType
        return None
    elif marshalType == 'l':
        n = unpack('i', fp.read(4))[0]
        if n == 0:
            return long(0)
        size = abs(n); 
        d = long(0)
        for j in range(0, size):
            md = int(unpack('h', fp.read(2))[0])
            d += md << j*15;
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
        raise KeyError, marshalType
        return None
    elif marshalType == '{':
        raise KeyError, marshalType
        return None
    elif marshalType in ['<', '>']:
        raise KeyError, marshalType
        return None
    else:
        sys.stderr.write("Unkown type %i (hex %x)\n" % (ord(marshalType), ord(marshalType)))
    
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
    dis(code)

if __name__ == "__main__":
    _test()
