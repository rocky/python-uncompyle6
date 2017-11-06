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

from uncompyle6.scanner import Token, parse_fn_counts
from xdis.code import iscode
from xdis.bytecode import Bytecode
import xdis
from array import array

# bytecode verification, verify(), uses JUMP_OPS from here
from xdis.opcodes import opcode_36 as opc
JUMP_OPS = opc.JUMP_OPS

class Scanner36(Scanner3):

    def __init__(self, show_asm=None):
        Scanner3.__init__(self, 3.6, show_asm)
        return

    def ingest(self, co, classname=None, code_objects={}, show_asm=None):
        tokens, customize = self.ingest_internal(co, classname, code_objects, show_asm)
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

    def ingest_internal(self, co, classname=None, code_objects={}, show_asm=None):
        """
        Pick out tokens from an uncompyle6 code object, and transform them,
        returning a list of uncompyle6 'Token's.

        The transformations are made to assist the deparsing grammar.
        Specificially:
           -  various types of LOAD_CONST's are categorized in terms of what they load
           -  COME_FROM instructions are added to assist parsing control structures
           -  MAKE_FUNCTION and FUNCTION_CALLS append the number of positional arguments

        Also, when we encounter certain tokens, we add them to a set which will cause custom
        grammar rules. Specifically, variable arg tokens like MAKE_FUNCTION or BUILD_LIST
        cause specific rules for the specific number of arguments they take.
        """

        # FIXME: remove this when all subsidiary functions have been removed.
        # We should be able to get everything from the self.insts list.
        self.code = array('B', co.co_code)

        show_asm = self.show_asm if not show_asm else show_asm
        # show_asm = 'both'
        if show_asm in ('both', 'before'):
            bytecode = Bytecode(co, self.opc)
            for instr in bytecode.get_instructions(co):
                print(instr.disassemble())

        # list of tokens/instructions
        tokens = []

        # "customize" is a dict whose keys are nonterminals
        # and the value is the argument stack entries for that
        # nonterminal. The count is a little hoaky. It is mostly
        # not used, but sometimes it is.
        customize = {}
        if self.is_pypy:
            customize['PyPy'] = 0

        self.build_lines_data(co)
        self.build_prev_op()

        bytecode = Bytecode(co, self.opc)

        # FIXME: put as its own method?
        # Scan for assertions. Later we will
        # turn 'LOAD_GLOBAL' to 'LOAD_ASSERT'.
        # 'LOAD_ASSERT' is used in assert statements.
        self.load_asserts = set()
        self.insts = list(bytecode)
        n = len(self.insts)
        for i, inst in enumerate(self.insts):
            # We need to detect the difference between
            # "raise AssertionError" and "assert"
            # If we have a JUMP_FORWARD after the
            # RAISE_VARARGS then we have a "raise" statement
            # else we have an "assert" statement.
            if inst.opname == 'POP_JUMP_IF_TRUE' and i+1 < n:
                next_inst = self.insts[i+1]
                if (next_inst.opname == 'LOAD_GLOBAL' and
                    next_inst.argval == 'AssertionError'):
                    if (i + 2 < n and self.insts[i+2].opname.startswith('RAISE_VARARGS')):
                        self.load_asserts.add(next_inst.offset)
                    pass
                pass

        # Get jump targets
        # Format: {target offset: [jump offsets]}
        jump_targets = self.find_jump_targets(show_asm)
        # print("XXX2", jump_targets)
        last_op_was_break = False

        for i, inst in enumerate(bytecode):

            argval = inst.argval
            op     = inst.opcode
            if op == self.opc.EXTENDED_ARG:
                continue

            if inst.offset in jump_targets:
                jump_idx = 0
                # We want to process COME_FROMs to the same offset to be in *descending*
                # offset order so we have the larger range or biggest instruction interval
                # last. (I think they are sorted in increasing order, but for safety
                # we sort them). That way, specific COME_FROM tags will match up
                # properly. For example, a "loop" with an "if" nested in it should have the
                # "loop" tag last so the grammar rule matches that properly.
                for jump_offset in sorted(jump_targets[inst.offset], reverse=True):
                    come_from_name = 'COME_FROM'
                    opname = self.opname_for_offset(jump_offset)
                    if opname.startswith('SETUP_'):
                        come_from_type = opname[len('SETUP_'):]
                        come_from_name = 'COME_FROM_%s' % come_from_type
                        pass
                    elif inst.offset in self.except_targets:
                        come_from_name = 'COME_FROM_EXCEPT_CLAUSE'
                    tokens.append(Token(come_from_name,
                                        None, repr(jump_offset),
                                        offset='%s_%s' % (inst.offset, jump_idx),
                                        has_arg = True, opc=self.opc))
                    jump_idx += 1
                    pass
                pass
            elif inst.offset in self.else_start:
                end_offset = self.else_start[inst.offset]
                tokens.append(Token('ELSE',
                                    None, repr(end_offset),
                                    offset='%s' % (inst.offset),
                                    has_arg = True, opc=self.opc))

                pass

            pattr  = inst.argrepr
            opname = inst.opname

            if opname in ['LOAD_CONST']:
                const = argval
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
            elif opname in ('MAKE_FUNCTION', 'MAKE_CLOSURE'):
                if self.version >= 3.6:
                    # 3.6+ doesn't have MAKE_CLOSURE, so opname == 'MAKE_FUNCTION'
                    flags = argval
                    opname = 'MAKE_FUNCTION_%d' % (flags)
                    attr = []
                    for flag in self.MAKE_FUNCTION_FLAGS:
                        bit = flags & 1
                        if bit:
                            if pattr:
                                pattr += ", " + flag
                            else:
                                pattr += flag
                        attr.append(bit)
                        flags >>= 1
                    attr = attr[:4] # remove last value: attr[5] == False
                else:
                    pos_args, name_pair_args, annotate_args = parse_fn_counts(inst.argval)
                    pattr = ("%d positional, %d keyword pair, %d annotated" %
                                 (pos_args, name_pair_args, annotate_args))
                    if name_pair_args > 0:
                        opname = '%s_N%d' % (opname, name_pair_args)
                        pass
                    if annotate_args > 0:
                        opname = '%s_A_%d' % (opname, annotate_args)
                        pass
                    opname = '%s_%d' % (opname, pos_args)
                    attr = (pos_args, name_pair_args, annotate_args)
                tokens.append(
                    Token(
                        opname = opname,
                        attr = attr,
                        pattr = pattr,
                        offset = inst.offset,
                        linestart = inst.starts_line,
                        op = op,
                        has_arg = inst.has_arg,
                        opc = self.opc
                    )
                )
                continue
            elif op in self.varargs_ops:
                pos_args = argval
                if self.is_pypy and not pos_args and opname == 'BUILD_MAP':
                    opname = 'BUILD_MAP_n'
                else:
                    opname = '%s_%d' % (opname, pos_args)
            elif self.is_pypy and opname in ('CALL_METHOD', 'JUMP_IF_NOT_DEBUG'):
                # The value in the dict is in special cases in semantic actions, such
                # as CALL_FUNCTION. The value is not used in these cases, so we put
                # in arbitrary value 0.
                customize[opname] = 0
            elif opname == 'UNPACK_EX':
                # FIXME: try with scanner and parser by
                # changing argval
                before_args = argval & 0xFF
                after_args = (argval >> 8) & 0xff
                pattr = "%d before vararg, %d after" % (before_args, after_args)
                argval = (before_args, after_args)
                opname = '%s_%d+%d' % (opname, before_args, after_args)

            elif op == self.opc.JUMP_ABSOLUTE:
                # Further classify JUMP_ABSOLUTE into backward jumps
                # which are used in loops, and "CONTINUE" jumps which
                # may appear in a "continue" statement.  The loop-type
                # and continue-type jumps will help us classify loop
                # boundaries The continue-type jumps help us get
                # "continue" statements with would otherwise be turned
                # into a "pass" statement because JUMPs are sometimes
                # ignored in rules as just boundary overhead. In
                # comprehensions we might sometimes classify JUMP_BACK
                # as CONTINUE, but that's okay since we add a grammar
                # rule for that.
                pattr = argval
                # FIXME: 0 isn't always correct
                target = self.get_target(inst.offset, 0)
                if target <= inst.offset:
                    next_opname = self.opname[self.code[inst.offset+3]]
                    if (inst.offset in self.stmts and
                        (self.version != 3.0 or (hasattr(inst, 'linestart'))) and
                        (next_opname not in ('END_FINALLY', 'POP_BLOCK',
                                            # Python 3.0 only uses POP_TOP
                                            'POP_TOP'))):
                        opname = 'CONTINUE'
                    else:
                        opname = 'JUMP_BACK'
                        # FIXME: this is a hack to catch stuff like:
                        #   if x: continue
                        # the "continue" is not on a new line.
                        # There are other situations where we don't catch
                        # CONTINUE as well.
                        if tokens[-1].kind == 'JUMP_BACK' and tokens[-1].attr <= argval:
                            if tokens[-2].kind == 'BREAK_LOOP':
                                del tokens[-1]
                            else:
                                # intern is used because we are changing the *previous* token
                                tokens[-1].kind = intern('CONTINUE')
                    if last_op_was_break and opname == 'CONTINUE':
                        last_op_was_break = False
                        continue
            elif op == self.opc.RETURN_VALUE:
                if inst.offset in self.return_end_ifs:
                    opname = 'RETURN_END_IF'
            elif inst.offset in self.load_asserts:
                opname = 'LOAD_ASSERT'

            last_op_was_break = opname == 'BREAK_LOOP'
            tokens.append(
                Token(
                    opname = opname,
                    attr = argval,
                    pattr = pattr,
                    offset = inst.offset,
                    linestart = inst.starts_line,
                    op = op,
                    has_arg = inst.has_arg,
                    opc = self.opc
                    )
                )
            pass

        if show_asm in ('both', 'after'):
            for t in tokens:
                print(t)
            print()
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
