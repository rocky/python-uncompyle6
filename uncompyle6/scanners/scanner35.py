#  Copyright (c) 2016 by Rocky Bernstein
"""
Python 3.5 bytecode scanner/deparser

This overlaps Python's 3.5's dis module, and in fact in some cases
we just fall back to that. But the intent is that it can be run from
Python 2 and other versions of Python. Also, we save token information
for later use in deparsing.
"""

from __future__ import print_function

import inspect
from array import array
import uncompyle6.scanners.scanner3 as scan3
import uncompyle6.scanners.dis35 as dis35

from uncompyle6.code import iscode
from uncompyle6.scanner import Token

import uncompyle6.opcodes.opcode_35
# verify uses JUMP_OPs from here
JUMP_OPs = uncompyle6.opcodes.opcode_35.JUMP_OPs

from uncompyle6.opcodes.opcode_35 import *

class Scanner35(scan3.Scanner3):

    # Note: we can't use built-in disassembly routines, unless
    # we do post-processing like we do here.
    def disassemble(self, co, classname=None,
                    code_objects={}):

        # imoprt dis; dis.disassemble(co) # DEBUG

        # Container for tokens
        tokens = []

        customize = {}
        self.code = array('B', co.co_code)
        self.build_lines_data(co)
        self.build_prev_op()

        bytecode = dis35.Bytecode(co)

        # self.lines contains (block,addrLastInstr)
        if classname:
            classname = '_' + classname.lstrip('_') + '__'

            def unmangle(name):
                if name.startswith(classname) and name[-2:] != '__':
                    return name[len(classname) - 2:]
                return name
        else:
            pass

        # Scan for assertions. Later we will
        # turn 'LOAD_GLOBAL' to 'LOAD_ASSERT' for those
        # assertions
        self.load_asserts = set()
        bs = list(bytecode)
        n = len(bs)
        for i in range(n):
            inst = bs[i]

            if inst.opname == 'POP_JUMP_IF_TRUE' and i+1 < n:
                next_inst = bs[i+1]
                if (next_inst.opname == 'LOAD_GLOBAL' and
                    next_inst.argval == 'AssertionError'):
                    self.load_asserts.add(next_inst.offset)

        # Get jump targets
        # Format: {target offset: [jump offsets]}
        jump_targets = self.find_jump_targets()

        for inst in bytecode:
            if inst.offset in jump_targets:
                jump_idx = 0
                for jump_offset in jump_targets[inst.offset]:
                    tokens.append(Token('COME_FROM', None, repr(jump_offset),
                                        offset='%s_%s' % (inst.offset, jump_idx)))
                    jump_idx += 1
                    pass
                pass

            pattr =  inst.argrepr
            opname = inst.opname

            if opname in ['LOAD_CONST']:
                const = inst.argval
                if iscode(const):
                    if const.co_name == '<lambda>':
                        opname = 'LOAD_LAMBDA'
                    elif const.co_name == '<genexpr>':
                        opname = 'LOAD_GENEXPR'
                    elif const.co_name == '<dictcomp>':
                        opname = 'LOAD_DICTCOMP'
                    elif const.co_name == '<setcomp>':
                        opname = 'LOAD_SETCOMP'
                    elif const.co_name == '<listcomp>':
                        opname = 'LOAD_LISTCOMP'
                    # verify() uses 'pattr' for comparison, since 'attr'
                    # now holds Code(const) and thus can not be used
                    # for comparison (todo: think about changing this)
                    # pattr = 'code_object @ 0x%x %s->%s' %\
                    # (id(const), const.co_filename, const.co_name)
                    pattr = '<code_object ' + const.co_name + '>'
                else:
                    pattr = const
                    pass
            elif opname == 'MAKE_FUNCTION':
                argc = inst.argval
                attr = ((argc & 0xFF), (argc >> 8) & 0xFF, (argc >> 16) & 0x7FFF)
                pos_args, name_pair_args, annotate_args = attr
                if name_pair_args > 0:
                    opname = 'MAKE_FUNCTION_N%d' % name_pair_args
                    pass
                if annotate_args > 0:
                    opname = '%s_A_%d' % [op_name, annotate_args]
                    pass
                opname = '%s_%d' % (opname, pos_args)
                pattr = ("%d positional, %d keyword pair, %d annotated" %
                             (pos_args, name_pair_args, annotate_args))
                tokens.append(
                    Token(
                        type_ = opname,
                        attr = (pos_args, name_pair_args, annotate_args),
                        pattr = pattr,
                        offset = inst.offset,
                        linestart = inst.starts_line)
                    )
                continue
            elif opname in ('BUILD_LIST', 'BUILD_TUPLE', 'BUILD_SET', 'BUILD_SLICE',
                            'BUILD_MAP', 'UNPACK_SEQUENCE', 'MAKE_CLOSURE',
                            'RAISE_VARARGS'
                            ):
                pos_args = inst.argval
                if inst.opname != 'BUILD_SLICE':
                    customize[opname] = pos_args
                    pass
                opname = '%s_%d' % (opname, pos_args)
            elif opname == 'JUMP_ABSOLUTE':
                pattr = inst.argval
                target = self.get_target(inst.offset)
                if target < inst.offset:
                    if (inst.offset in self.stmts and
                        self.code[inst.offset+3] not in (END_FINALLY, POP_BLOCK)
                        and inst.offset not in self.not_continue):
                        opname = 'CONTINUE'
                    else:
                        opname = 'JUMP_BACK'

            elif inst.offset in self.load_asserts:
                opname = 'LOAD_ASSERT'

            tokens.append(
                Token(
                    type_ = opname,
                    attr = inst.argval,
                    pattr = pattr,
                    offset = inst.offset,
                    linestart = inst.starts_line,
                    )
                )
            pass
        return tokens, {}

if __name__ == "__main__":
    co = inspect.currentframe().f_code
    tokens, customize = Scanner35(3.5).disassemble(co)
    for t in tokens:
        print(t)
    pass
