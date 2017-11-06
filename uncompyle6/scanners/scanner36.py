#  Copyright (c) 2016-2017 by Rocky Bernstein
"""
Python 3.6 bytecode decompiler scanner

Does some additional massaging of xdis-disassembled instructions to
make things easier for decompilation.

This sets up opcodes Python's 3.6 and calls a generalized
scanner routine for Python 3.
"""

from __future__ import print_function

from uncompyle6.scanners.scanner3 import Scanner3

import xdis

# bytecode verification, verify(), uses JUMP_OPS from here
from xdis.opcodes import opcode_36 as opc
JUMP_OPS = opc.JUMP_OPS

class Scanner36(Scanner3):

    def __init__(self, show_asm=None):
        Scanner3.__init__(self, 3.6, show_asm)
        return

    def ingest(self, co, classname=None, code_objects={}, show_asm=None):
        tokens, customize = Scanner3.ingest(self, co, classname, code_objects, show_asm)
        for t in tokens:
            # The lowest bit of flags indicates whether the
            # var-keyword argument is placed at the top of the stack
            if t.op == self.opc.CALL_FUNCTION_EX and t.attr & 1:
                t.type = 'CALL_FUNCTION_EX_KW'
                pass
            elif t.op == self.opc.CALL_FUNCTION_KW:
                t.type = 'CALL_FUNCTION_KW_{t.attr}'.format(**locals())
            elif t.op == self.opc.BUILD_TUPLE_UNPACK_WITH_CALL:
                t.type = 'BUILD_TUPLE_UNPACK_WITH_CALL_%d' % t.attr
            elif t.op == self.opc.BUILD_MAP_UNPACK_WITH_CALL:
                t.type = 'BUILD_MAP_UNPACK_WITH_CALL_%d' % t.attr
            pass
        return tokens, customize

    def find_jump_targets(self, debug):
        """
        Detect all offsets in a byte code which are jump targets
        where we might insert a COME_FROM instruction.

        Return the list of offsets.

        Return the list of offsets. An instruction can be jumped
        to in from multiple instructions.
        """
        code = self.code
        n = len(code)
        self.structs = [{'type':  'root',
                         'start': 0,
                         'end':   n-1}]

        # All loop entry points
        self.loops = []

        # Map fixed jumps to their real destination
        self.fixed_jumps = {}
        self.except_targets = {}
        self.ignore_if = set()
        self.build_statement_indices()
        self.else_start = {}

        # Containers filled by detect_control_flow()
        self.not_continue = set()
        self.return_end_ifs = set()
        self.setup_loop_targets = {}  # target given setup_loop offset
        self.setup_loops = {}  # setup_loop offset given target

        targets = {}
        extended_arg = 0
        for i, inst in enumerate(self.insts):
            offset = inst.offset
            op = inst.opcode

            self.detect_control_flow(offset, targets, extended_arg)

            if inst.has_arg:
                label = self.fixed_jumps.get(offset)
                oparg = inst.arg
                next_offset = xdis.next_offset(op, self.opc, offset)

                if label is None:
                    if op in self.opc.hasjrel and op != self.opc.FOR_ITER:
                        label = next_offset + oparg
                    elif op in self.opc.hasjabs:
                        if op in self.jump_if_pop:
                            if oparg > offset:
                                label = oparg

                if label is not None and label != -1:
                    targets[label] = targets.get(label, []) + [offset]
            elif op == self.opc.END_FINALLY and offset in self.fixed_jumps:
                label = self.fixed_jumps[offset]
                targets[label] = targets.get(label, []) + [offset]
                pass

            extended_arg = 0
            pass # for loop

        # DEBUG:
        if debug in ('both', 'after'):
            import pprint as pp
            pp.pprint(self.structs)

        return targets

    pass

if __name__ == "__main__":
    from uncompyle6 import PYTHON_VERSION
    if PYTHON_VERSION == 3.6:
        import inspect
        co = inspect.currentframe().f_code
        tokens, customize = Scanner36().ingest(co)
        for t in tokens:
            print(t.format())
        pass
    else:
        print("Need to be Python 3.6 to demo; I am %s." %
              PYTHON_VERSION)
