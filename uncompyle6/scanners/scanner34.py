#  Copyright (c) 2015-2016 by Rocky Bernstein
"""
Python 3.4 bytecode scanner/deparser

This overlaps Python's 3.4's dis module, and in fact in some cases
we just fall back to that. But the intent is that it can be run from
Python 2 and other versions of Python. Also, we save token information
for later use in deparsing.
"""

from __future__ import print_function

import dis, inspect
from array import array
import uncompyle6.scanners.scanner3 as scan3

from uncompyle6 import PYTHON_VERSION
from uncompyle6.code import iscode
from uncompyle6.scanner import Token

# Get all the opcodes into globals
globals().update(dis.opmap)

import uncompyle6.opcodes.opcode_34
# verify uses JUMP_OPs from here
JUMP_OPs = uncompyle6.opcodes.opcode_34.JUMP_OPs

from uncompyle6.opcodes.opcode_34 import *

class Scanner34(scan3.Scanner3):

    def disassemble(self, co, classname=None, code_objects={}):
        fn = self.disassemble_built_in if PYTHON_VERSION == 3.4 \
            else self.disassemble_generic
        return fn(co, classname, code_objects=code_objects)

    def disassemble_built_in(self, co, classname=None,
                             code_objects={}):
        # Container for tokens
        tokens = []
        customize = {}
        self.code = array('B', co.co_code)
        self.build_lines_data(co)
        self.build_prev_op()

        # Get jump targets
        # Format: {target offset: [jump offsets]}
        jump_targets = self.find_jump_targets()
        bytecode = dis.Bytecode(co)

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
            if inst.opname == 'POP_JUMP_IF_TRUE' and  i+1 < n:
                next_inst = bs[i+1]
                if (next_inst.opname == 'LOAD_GLOBAL' and
                    next_inst.argval == 'AssertionError'):
                    self.load_asserts.add(next_inst.offset)

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
                            'UNPACK_SEQUENCE',
                            'MAKE_CLOSURE',
                            'RAISE_VARARGS'
                            ):
                # if opname == 'BUILD_TUPLE' and \
                #     self.code[self.prev[offset]] == LOAD_CLOSURE:
                #     continue
                # else:
                #     op_name = '%s_%d' % (op_name, oparg)
                #     if opname != BUILD_SLICE:
                #         customize[op_name] = oparg
                opname = '%s_%d' % (opname, inst.argval)
                if inst.opname != 'BUILD_SLICE':
                    customize[opname] = inst.argval

            elif opname == 'JUMP_ABSOLUTE':
                pattr = inst.argval
                target = self.get_target(inst.offset)
                if target < inst.offset:
                    if (inst.offset in self.stmts and
                        self.code[inst.offset+3] not in (END_FINALLY, POP_BLOCK)
                        and offset not in self.not_continue):
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
    tokens, customize = Scanner34(3.4).disassemble(co)
    for t in tokens:
        print(t)
    pass
