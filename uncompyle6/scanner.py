#  Copyright (c) 2016 by Rocky Bernstein
#  Copyright (c) 2005 by Dan Pascu <dan@windowmaker.org>
#  Copyright (c) 2000-2002 by hartmut Goebel <h.goebel@crazy-compilers.com>
#  Copyright (c) 1999 John Aycock
#
#  See LICENSE
#
"""
scanner/ingestion module. From here we call various version-specific
scanners, e.g. for Python 2.7 or 3.4.
"""

from __future__ import print_function

import sys

from uncompyle6 import PYTHON3, IS_PYPY
from uncompyle6.scanners.tok import Token
from xdis.bytecode import op_size
from xdis.magics import py_str2float
from xdis.util import code2num

# The byte code versions we support
PYTHON_VERSIONS = (1.5,
                   2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7,
                   3.0, 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7)

# FIXME: DRY
if PYTHON3:
    intern = sys.intern
    L65536 = 65536

    def long(l):
        return l
else:
    L65536 = long(65536) # NOQA

class Code(object):
    '''
    Class for representing code-objects.

    This is similar to the original code object, but additionally
    the diassembled code is stored in the attribute '_tokens'.
    '''
    def __init__(self, co, scanner, classname=None):
        for i in dir(co):
            if i.startswith('co_'):
                setattr(self, i, getattr(co, i))
        self._tokens, self._customize = scanner.ingest(co, classname)

class Scanner(object):

    def __init__(self, version, show_asm=None, is_pypy=False):
        self.version = version
        self.show_asm = show_asm
        self.is_pypy = is_pypy

        if version in PYTHON_VERSIONS:
            if is_pypy:
                v_str = "opcode_%spypy" % (int(version * 10))
            else:
                v_str = "opcode_%s" % (int(version * 10))
            exec("from xdis.opcodes import %s" % v_str)
            exec("self.opc = %s" % v_str)
        else:
            raise TypeError("%s is not a Python version I know about" % version)

        self.opname = self.opc.opname

        # FIXME: This weird Python2 behavior is not Python3
        self.resetTokenClass()

    def opname_for_offset(self, offset):
        return self.opc.opname[self.code[offset]]

    def op_name(self, op):
        return self.opc.opname[op]

    def is_jump_forward(self, offset):
        """
        Return True if the code at offset is some sort of jump forward.
        That is, it is ether "JUMP_FORWARD" or an absolute jump that
        goes forward.
        """
        if self.code[offset] == self.opc.JUMP_FORWARD:
            return True
        if self.code[offset] != self.opc.JUMP_ABSOLUTE:
            return False
        # FIXME 0 isn't always correct
        return offset < self.get_target(offset, 0)

    def get_target(self, pos, op=None):
        if op is None:
            op = self.code[pos]
        target = self.get_argument(pos)
        if op in self.opc.JREL_OPS:
            target += pos + 3
        return target

    # FIXME: the below can be removed after xdis version 3.6.1 has been released
    def extended_arg_val(self, val):
        return val << self.opc.EXTENDED_ARG_SHIFT

    def get_argument(self, pos):
        arg = self.code[pos+1] + self.code[pos+2] * 256
        return arg

    def print_bytecode(self):
        for i in self.op_range(0, len(self.code)):
            op = self.code[i]
            if op in self.JUMP_OPS:
                dest = self.get_target(i, op)
                print('%i\t%s\t%i' % (i, self.opname[op], dest))
            else:
                print('%i\t%s\t' % (i, self.opname[op]))

    def first_instr(self, start, end, instr, target=None, exact=True):
        """
        Find the first <instr> in the block from start to end.
        <instr> is any python bytecode instruction or a list of opcodes
        If <instr> is an opcode with a target (like a jump), a target
        destination can be specified which must match precisely if exact
        is True, or if exact is False, the instruction which has a target
        closest to <target> will be returned.

        Return index to it or None if not found.
        """
        code = self.code
        assert(start >= 0 and end <= len(code))

        try:
            None in instr
        except:
            instr = [instr]

        result_offset = None
        current_distance = len(code)
        for offset in self.op_range(start, end):
            op = code[offset]
            if op in instr:
                if target is None:
                    return offset
                dest = self.get_target(offset)
                if dest == target:
                    return offset
                elif not exact:
                    new_distance = abs(target - dest)
                    if new_distance < current_distance:
                        current_distance = new_distance
                        result_offset = offset
        return result_offset

    def last_instr(self, start, end, instr, target=None, exact=True):
        """
        Find the last <instr> in the block from start to end.
        <instr> is any python bytecode instruction or a list of opcodes
        If <instr> is an opcode with a target (like a jump), a target
        destination can be specified which must match precisely if exact
        is True, or if exact is False, the instruction which has a target
        closest to <target> will be returned.

        Return index to it or None if not found.
        """

        code = self.code
        # Make sure requested positions do not go out of
        # code bounds
        if not (start>=0 and end<=len(code)):
            return None

        try:
            None in instr
        except:
            instr = [instr]

        result_offset = None
        current_distance = len(code)
        extended_arg = 0
        for offset in self.op_range(start, end):
            op = code[offset]

            if op == self.opc.EXTENDED_ARG:
                arg = code2num(code, offset+1) | extended_arg
                extended_arg = self.extended_arg_val(arg)
                continue

            if op in instr:
                if target is None:
                    result_offset = offset
                else:
                    dest = self.get_target(offset, extended_arg)
                    if dest == target:
                        current_distance = 0
                        result_offset = offset
                    elif not exact:
                        new_distance = abs(target - dest)
                        if new_distance <= current_distance:
                            current_distance = new_distance
                            result_offset = offset
        return result_offset

    def all_instr(self, start, end, instr, target=None, include_beyond_target=False):
        """
        Find all <instr> in the block from start to end.
        <instr> is any python bytecode instruction or a list of opcodes
        If <instr> is an opcode with a target (like a jump), a target
        destination can be specified which must match precisely.

        Return a list with indexes to them or [] if none found.
        """
        code = self.code
        assert(start >= 0 and end <= len(code))

        try:
            None in instr
        except:
            instr = [instr]

        result = []
        extended_arg = 0
        for offset in self.op_range(start, end):

            op = code[offset]

            if op == self.opc.EXTENDED_ARG:
                arg = code2num(code, offset+1) | extended_arg
                extended_arg = self.extended_arg_val(arg)
                continue

            if op in instr:
                if target is None:
                    result.append(offset)
                else:
                    t = self.get_target(offset, extended_arg)
                    if include_beyond_target and t >= target:
                        result.append(offset)
                    elif t == target:
                        result.append(offset)
                        pass
                    pass
                pass
            extended_arg = 0
            pass

        return result

    def op_range(self, start, end):
        """
        Iterate through positions of opcodes, skipping
        arguments.
        """
        while start < end:
            yield start
            start += op_size(self.code[start], self.opc)

    def remove_mid_line_ifs(self, ifs):
        """
        Go through passed offsets, filtering ifs
        located somewhere mid-line.
        """
        filtered = []
        for i in ifs:
            # For each offset, if line number of current and next op
            # is the same
            if self.lines[i].l_no == self.lines[i+3].l_no:
                # Skip last op on line if it is some sort of POP_JUMP.
                if self.code[self.prev[self.lines[i].next]] in (self.opc.PJIT, self.opc.PJIF):
                    continue
            filtered.append(i)
        return filtered

    def resetTokenClass(self):
        return self.setTokenClass(Token)

    def restrict_to_parent(self, target, parent):
        """Restrict target to parent structure boundaries."""
        if not (parent['start'] < target < parent['end']):
            target = parent['end']
        return target

    def setTokenClass(self, tokenClass):
        # assert isinstance(tokenClass, types.ClassType)
        self.Token = tokenClass
        return self.Token

def parse_fn_counts(argc):
    return ((argc & 0xFF), (argc >> 8) & 0xFF, (argc >> 16) & 0x7FFF)


def get_scanner(version, is_pypy=False, show_asm=None):

    # If version is a string, turn that into the corresponding float.
    if isinstance(version, str):
        version = py_str2float(version)

    # Pick up appropriate scanner
    if version in PYTHON_VERSIONS:
        v_str = "%s" % (int(version * 10))
        if PYTHON3:
            import importlib
            if is_pypy:
                scan = importlib.import_module("uncompyle6.scanners.pypy%s" % v_str)
            else:
                scan = importlib.import_module("uncompyle6.scanners.scanner%s" % v_str)
            if False: print(scan)  # Avoid unused scan
        else:
            if is_pypy:
                exec("import uncompyle6.scanners.pypy%s as scan" % v_str)
            else:
                exec("import uncompyle6.scanners.scanner%s as scan" % v_str)
        if is_pypy:
            scanner = eval("scan.ScannerPyPy%s(show_asm=show_asm)" % v_str)
        else:
            scanner = eval("scan.Scanner%s(show_asm=show_asm)" % v_str)
    else:
        raise RuntimeError("Unsupported Python version %s" % version)
    return scanner

if __name__ == "__main__":
    import inspect, uncompyle6
    co = inspect.currentframe().f_code
    scanner = get_scanner('2.7.13', True)
    scanner = get_scanner(sys.version[:5], False)
    scanner = get_scanner(uncompyle6.PYTHON_VERSION, IS_PYPY, True)
    tokens, customize = scanner.ingest(co, {})
