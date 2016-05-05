# (C) Copyright 2016 by Rocky Bernstein
"""
CPython 3.5 bytecode opcodes

used in scanner (bytecode disassembly) and parser (Python grammar)

This is a superset of Python 3.5's opcode.py with some opcodes that simplify
parsing and semantic interpretation.
"""

from copy import deepcopy

import uncompyle6.opcodes.opcode_3x as opcode_3x
from uncompyle6.opcodes.opcode_3x import fields2copy, hasfree, rm_op

# FIXME: can we DRY this even more?

opmap = {}
opname = [''] * 256
hasconst = []
hasjrel = []
hasjabs = []

def def_op(name, op):
    opname[op] = name
    opmap[name] = op

for object in fields2copy:
    globals()[object] =  deepcopy(getattr(opcode_3x, object))

# Below are opcodes changes since Python 3.2

rm_op(opname, opmap, 'STOP_CODE', 0)
rm_op(opname, opmap, 'STORE_LOCALS', 69)

# These are new since Python 3.3
def_op('YIELD_FROM', 72)
def_op('LOAD_CLASSDEREF', 148)

# These are removed since Python 3.4
rm_op(opname, opmap, 'WITH_CLEANUP', 81)

# These are new since Python 3.4
def_op('BINARY_MATRIX_MULTIPLY', 16)
def_op('INPLACE_MATRIX_MULTIPLY', 17)
def_op('GET_AITER', 50)
def_op('GET_ANEXT', 51)
def_op('BEFORE_ASYNC_WITH', 52)
def_op('GET_YIELD_FROM_ITER', 69)
def_op('GET_AWAITABLE', 73)
def_op('WITH_CLEANUP_START', 81)
def_op('WITH_CLEANUP_FINISH', 82)
def_op('BUILD_LIST_UNPACK', 149)
def_op('BUILD_MAP_UNPACK', 150)
def_op('BUILD_MAP_UNPACK_WITH_CALL', 151)
def_op('BUILD_TUPLE_UNPACK', 152)
def_op('BUILD_SET_UNPACK', 153)
def_op('SETUP_ASYNC_WITH', 154)


hasfree.append(148)

def updateGlobal():
    # JUMP_OPs are used in verification are set in the scanner
    # and used in the parser grammar
    globals().update({'PJIF': opmap['POP_JUMP_IF_FALSE']})
    globals().update({'PJIT': opmap['POP_JUMP_IF_TRUE']})
    globals().update({'JA': opmap['JUMP_ABSOLUTE']})
    globals().update({'JF': opmap['JUMP_FORWARD']})
    globals().update(dict([(k.replace('+', '_'), v) for (k, v) in opmap.items()]))
    globals().update({'JUMP_OPs': map(lambda op: opname[op], hasjrel + hasjabs)})

updateGlobal()

# FIXME: turn into pytest test
from uncompyle6 import PYTHON_VERSION
if PYTHON_VERSION == 3.5:
    import dis
    for item in dis.opmap.items():
        if item not in opmap.items():
            print(item)
    assert all(item in opmap.items() for item in dis.opmap.items())

# opcode_3x.dump_opcodes(opmap)
