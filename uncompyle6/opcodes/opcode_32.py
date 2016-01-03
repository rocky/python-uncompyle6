"""
CPython 3.2 bytecode opcodes

This is used in scanner (bytecode disassembly) and parser (Python grammar).

This is a superset of Python 3.2's opcode.py with some opcodes that simplify
parsing and semantic interpretation.
"""

from copy import deepcopy

import uncompyle6.opcodes.opcode_3x as opcode_3x
from uncompyle6.opcodes.opcode_3x import fields2copy

# FIXME: can we DRY this even more?

opmap = {}
opname = [''] * 256
hasjrel = []
hasjabs = []

for object in fields2copy:
    globals()[object] =  deepcopy(getattr(opcode_3x, object))

# There are no opcodes to add or change.
# If there were, they'd be listed below.

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

from uncompyle6 import PYTHON_VERSION
if PYTHON_VERSION == 3.2:
    import dis
    # for item in dis.opmap.items():
    #     if item not in opmap.items():
    #         print(item)
    assert all(item in opmap.items() for item in dis.opmap.items())

# opcode_3x.dump_opcodes(opmap)
