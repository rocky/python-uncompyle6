#  Copyright (c) 2015, 2016 by Rocky Bernstein
#  Copyright (c) 2005 by Dan Pascu <dan@windowmaker.org>
#  Copyright (c) 2000-2002 by hartmut Goebel <h.goebel@crazy-compilers.com>
"""
Python 3 Generic bytecode scanner/deparser

This overlaps various Python3's dis module, but it can be run from
Python versions other than the version running this code. Notably,
run from Python version 2.

Also we *modify* the instruction sequence to assist deparsing code.
For example:
 -  we add "COME_FROM" instructions to help in figuring out
    conditional branching and looping.
 -  LOAD_CONSTs are classified further into the type of thing
    they load:
      lambda's, genexpr's, {dict,set,list} comprehension's,
 -  PARAMETER counts appended  {CALL,MAKE}_FUNCTION, BUILD_{TUPLE,SET,SLICE}

Finally we save token information.
"""

from __future__ import print_function

from collections import namedtuple
from array import array

from xdis.code import iscode
from xdis.bytecode import Bytecode, findlinestarts
from uncompyle6.scanner import Token, parse_fn_counts

# Get all the opcodes into globals
import xdis.opcodes.opcode_33 as op3

import sys
from uncompyle6 import PYTHON3
if PYTHON3:
    intern = sys.intern

globals().update(op3.opmap)

# POP_JUMP_IF is used by verify
POP_JUMP_TF = (POP_JUMP_IF_TRUE, POP_JUMP_IF_FALSE)

import uncompyle6.scanner as scan

class Scanner3(scan.Scanner):

    def __init__(self, version, show_asm=None):
        super(Scanner3, self).__init__(version, show_asm)

        # Create opcode classification sets
        # Note: super initilization above initializes self.opc

        # Opcodes that can start a statement.
        self.statement_opcodes = frozenset([
            self.opc.SETUP_LOOP,    self.opc.BREAK_LOOP, self.opc.CONTINUE_LOOP,
            self.opc.SETUP_FINALLY, self.opc.END_FINALLY, self.opc.SETUP_EXCEPT,
            self.opc.SETUP_WITH,
            self.opc.POP_BLOCK,     self.opc.STORE_FAST, self.opc.DELETE_FAST,
            self.opc.STORE_DEREF,

            self.opc.STORE_GLOBAL, self.opc.DELETE_GLOBAL, self.opc.STORE_NAME,
            self.opc.DELETE_NAME,

            self.opc.STORE_ATTR, self.opc.DELETE_ATTR, self.opc.STORE_SUBSCR,
            self.opc.DELETE_SUBSCR,

            self.opc.RETURN_VALUE, self.opc.RAISE_VARARGS, self.opc.POP_TOP,
            self.opc.PRINT_EXPR,   self.opc.JUMP_ABSOLUTE
        ])

        # Opcodes that can start a designator non-terminal.
        # FIXME: JUMP_ABSOLUTE is weird. What's up with that?
        self.designator_ops = frozenset([
            self.opc.STORE_FAST,    self.opc.STORE_NAME, self.opc.STORE_GLOBAL,
            self.opc.STORE_DEREF,   self.opc.STORE_ATTR,
            self.opc.STORE_SUBSCR,  self.opc.UNPACK_SEQUENCE,
            self.opc.JUMP_ABSOLUTE, self.opc.UNPACK_EX
        ])

        self.jump_if_pop = frozenset([self.opc.JUMP_IF_FALSE_OR_POP,
                                      self.opc.JUMP_IF_TRUE_OR_POP])

        self.pop_jump_if_pop = frozenset([self.opc.JUMP_IF_FALSE_OR_POP,
                                          self.opc.JUMP_IF_TRUE_OR_POP,
                                          self.opc.POP_JUMP_IF_TRUE,
                                          self.opc.POP_JUMP_IF_FALSE])

        # Opcodes that take a variable number of arguments
        # (expr's)
        self.varargs = frozenset([self.opc.BUILD_LIST,
                                  self.opc.BUILD_TUPLE,
                                  self.opc.BUILD_SET,
                                  self.opc.BUILD_SLICE,
                                  self.opc.BUILD_MAP,
                                  self.opc.UNPACK_SEQUENCE,
                                  self.opc.RAISE_VARARGS])

        # Not really a set, but still clasification-like
        self.statement_opcode_sequences = [
            (self.opc.POP_JUMP_IF_FALSE, self.opc.JUMP_FORWARD),
            (self.opc.POP_JUMP_IF_FALSE, self.opc.JUMP_ABSOLUTE),
            (self.opc.POP_JUMP_IF_TRUE,  self.opc.JUMP_FORWARD),
            (self.opc.POP_JUMP_IF_TRUE,  self.opc.JUMP_ABSOLUTE)]


    def disassemble(self, co, classname=None, code_objects={}, show_asm=None):
        """
        Disassemble a Python 3 code object, returning a list of 'Token'.
        Various tranformations are made to assist the deparsing grammar.
        For example:
           -  various types of LOAD_CONST's are categorized in terms of what they load
           -  COME_FROM instructions are added to assist parsing control structures
           -  MAKE_FUNCTION and FUNCTION_CALLS append the number of positional aruments
        The main part of this procedure is modelled after
        dis.disassemble().
        """

        show_asm = self.show_asm if not show_asm else show_asm
        # show_asm = 'both'
        if show_asm in ('both', 'before'):
            bytecode = Bytecode(co, self.opc)
            for instr in bytecode.get_instructions(co):
                print(instr._disassemble())

        # Container for tokens
        tokens = []

        self.code = array('B', co.co_code)
        self.build_lines_data(co)
        self.build_prev_op()

        bytecode = Bytecode(co, self.opc)

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

            argval = inst.argval
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
            op = inst.opcode

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
            elif opname in ('MAKE_FUNCTION', 'MAKE_CLOSURE'):
                pos_args, name_pair_args, annotate_args = parse_fn_counts(inst.argval)
                if name_pair_args > 0:
                    opname = '%s_N%d' % (opname, name_pair_args)
                    pass
                if annotate_args > 0:
                    opname = '%s_A_%d' % [opname, annotate_args]
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
            elif op in self.varargs:
                pos_args = inst.argval
                opname = '%s_%d' % (opname, pos_args)
            elif opname == 'UNPACK_EX':
                # FIXME: try with scanner and parser by
                # changing inst.argval
                before_args = inst.argval & 0xFF
                after_args = (inst.argval >> 8) & 0xff
                pattr = "%d before vararg, %d after" % (before_args, after_args)
                argval = (before_args, after_args)
                opname = '%s_%d+%d' % (opname, before_args, after_args)
            elif op == self.opc.JUMP_ABSOLUTE:
                # Further classifhy JUMP_ABSOLUTE into backward jumps
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
                pattr = inst.argval
                target = self.get_target(inst.offset)
                if target <= inst.offset:
                    next_opname = self.opname[self.code[inst.offset+3]]
                    if (inst.offset in self.stmts and
                        next_opname not in ('END_FINALLY', 'POP_BLOCK')
                        and inst.offset not in self.not_continue):
                        opname = 'CONTINUE'
                    else:
                        opname = 'JUMP_BACK'
                        # FIXME: this is a hack to catch stuff like:
                        #   if x: continue
                        # the "continue" is not on a new line.
                        # There are other situations were we don't catch
                        # CONTINUE as well.
                        if tokens[-1].type == 'JUMP_BACK':
                            tokens[-1].type = intern('CONTINUE')

            elif op == self.opc.RETURN_VALUE:
                if inst.offset in self.return_end_ifs:
                    opname = 'RETURN_END_IF'
            elif inst.offset in self.load_asserts:
                opname = 'LOAD_ASSERT'

            tokens.append(
                Token(
                    type_ = opname,
                    attr = argval,
                    pattr = pattr,
                    offset = inst.offset,
                    linestart = inst.starts_line,
                    )
                )
            pass
        return tokens, {}

    def build_lines_data(self, code_obj):
        """
        Generate various line-related helper data.
        """
        # Offset: lineno pairs, only for offsets which start line.
        # Locally we use list for more convenient iteration using indices
        linestarts = list(findlinestarts(code_obj))
        self.linestarts = dict(linestarts)
        # Plain set with offsets of first ops on line
        self.linestart_offsets = set(a for (a, _) in linestarts)
        # 'List-map' which shows line number of current op and offset of
        # first op on following line, given offset of op as index
        self.lines = lines = []
        LineTuple = namedtuple('LineTuple', ['l_no', 'next'])
        # Iterate through available linestarts, and fill
        # the data for all code offsets encountered until
        # last linestart offset
        _, prev_line_no = linestarts[0]
        offset = 0
        for start_offset, line_no in linestarts[1:]:
            while offset < start_offset:
                lines.append(LineTuple(prev_line_no, start_offset))
                offset += 1
            prev_line_no = line_no
        # Fill remaining offsets with reference to last line number
        # and code length as start offset of following non-existing line
        codelen = len(self.code)
        while offset < codelen:
            lines.append(LineTuple(prev_line_no, codelen))
            offset += 1

    def build_prev_op(self):
        """
        Compose 'list-map' which allows to jump to previous
        op, given offset of current op as index.
        """
        code = self.code
        codelen = len(code)
        # 2.x uses prev 3.x uses prev_op. Sigh
        # Until we get this sorted out.
        self.prev = self.prev_op = [0]
        for offset in self.op_range(0, codelen):
            op = code[offset]
            for _ in range(self.op_size(op)):
                self.prev_op.append(offset)

    def op_size(self, op):
        """
        Return size of operator with its arguments
        for given opcode <op>.
        """
        if op < self.opc.HAVE_ARGUMENT:
            return 1
        else:
            return 3

    def find_jump_targets(self):
        """
        Detect all offsets in a byte code which are jump targets.

        Return the list of offsets.

        This procedure is modelled after dis.findlabels(), but here
        for each target the number of jumps is counted.
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
        self.ignore_if = set()
        self.build_statement_indices()

        # Containers filled by detect_structure()
        self.not_continue = set()
        self.return_end_ifs = set()

        targets = {}
        for offset in self.op_range(0, n):
            op = code[offset]

            # Determine structures and fix jumps in Python versions
            # since 2.3
            self.detect_structure(offset)

            if op >= op3.HAVE_ARGUMENT:
                label = self.fixed_jumps.get(offset)
                oparg = code[offset+1] + code[offset+2] * 256

                if label is None:
                    if op in op3.hasjrel and op != self.opc.FOR_ITER:
                        label = offset + self.op_size(op) + oparg
                    elif op in op3.hasjabs:
                        if op in self.jump_if_pop:
                            if oparg > offset:
                                label = oparg

                if label is not None and label != -1:
                    targets[label] = targets.get(label, []) + [offset]
            elif op == self.opc.END_FINALLY and offset in self.fixed_jumps:
                label = self.fixed_jumps[offset]
                targets[label] = targets.get(label, []) + [offset]
        return targets

    def build_statement_indices(self):
        code = self.code
        start = 0
        end = codelen = len(code)

        # Compose preliminary list of indices with statements,
        # using plain statement opcodes
        prelim = self.all_instr(start, end, self.statement_opcodes)

        # Initialize final container with statements with
        # preliminnary data
        stmts = self.stmts = set(prelim)

        # Same for opcode sequences
        pass_stmts = set()
        for sequence in self.statement_opcode_sequences:
            for i in self.op_range(start, end-(len(sequence)+1)):
                match = True
                for elem in sequence:
                    if elem != code[i]:
                        match = False
                        break
                    i += self.op_size(code[i])

                if match is True:
                    i = self.prev_op[i]
                    stmts.add(i)
                    pass_stmts.add(i)

        # Initialize statement list with the full data we've gathered so far
        if pass_stmts:
            stmt_offset_list = list(stmts)
            stmt_offset_list.sort()
        else:
            stmt_offset_list = prelim
        # 'List-map' which contains offset of start of
        # next statement, when op offset is passed as index
        self.next_stmt = slist = []
        last_stmt_offset = -1
        i = 0
        # Go through all statement offsets
        for stmt_offset in stmt_offset_list:
            # Process absolute jumps, but do not remove 'pass' statements
            # from the set
            if (code[stmt_offset] == self.opc.JUMP_ABSOLUTE
                and stmt_offset not in pass_stmts):
                # If absolute jump occurs in forward direction or it takes off from the
                # same line as previous statement, this is not a statement
                target = self.get_target(stmt_offset)
                if target > stmt_offset or self.lines[last_stmt_offset].l_no == self.lines[stmt_offset].l_no:
                    stmts.remove(stmt_offset)
                    continue
                # Rewing ops till we encounter non-JUMP_ABSOLUTE one
                j = self.prev_op[stmt_offset]
                while code[j] == self.opc.JUMP_ABSOLUTE:
                    j = self.prev_op[j]
                # If we got here, then it's list comprehension which
                # is not a statement too
                if code[j] == self.opc.LIST_APPEND:
                    stmts.remove(stmt_offset)
                    continue
            # Exclude ROT_TWO + POP_TOP
            elif (code[stmt_offset] == self.opc.POP_TOP
                  and code[self.prev_op[stmt_offset]] == self.opc.ROT_TWO):
                stmts.remove(stmt_offset)
                continue
            # Exclude FOR_ITER + designators
            elif code[stmt_offset] in self.designator_ops:
                j = self.prev_op[stmt_offset]
                while code[j] in self.designator_ops:
                    j = self.prev_op[j]
                if code[j] == self.opc.FOR_ITER:
                    stmts.remove(stmt_offset)
                    continue
            # Add to list another list with offset of current statement,
            # equal to length of previous statement
            slist += [stmt_offset] * (stmt_offset-i)
            last_stmt_offset = stmt_offset
            i = stmt_offset
        # Finish filling the list for last statement
        slist += [codelen] * (codelen-len(slist))

    def get_target(self, offset):
        """
        Get target offset for op located at given <offset>.
        """
        op = self.code[offset]
        target = self.code[offset+1] + self.code[offset+2] * 256
        if op in op3.hasjrel:
            target += offset + 3
        return target

    def detect_structure(self, offset):
        """
        Detect structures and their boundaries to fix optimized jumps
        in python2.3+
        """

        # TODO: check the struct boundaries more precisely -Dan

        code = self.code
        op = code[offset]

        # Detect parent structure
        parent = self.structs[0]
        start = parent['start']
        end = parent['end']

        # Pick inner-most parent for our offset
        for struct in self.structs:
            current_start = struct['start']
            current_end   = struct['end']
            if ((current_start <= offset < current_end)
                and (current_start >= start and current_end <= end)):
                start = current_start
                end = current_end
                parent = struct

        if op == self.opc.SETUP_LOOP:
            start = offset+3
            target = self.get_target(offset)
            end    = self.restrict_to_parent(target, parent)

            if target != end:
                self.fixed_jumps[offset] = end
            (line_no, next_line_byte) = self.lines[offset]
            jump_back = self.last_instr(start, end, self.opc.JUMP_ABSOLUTE,
                                          next_line_byte, False)

            if jump_back and jump_back != self.prev_op[end] and self.is_jump_forward(jump_back+3):
                if (code[self.prev_op[end]] == self.opc.RETURN_VALUE
                    or (code[self.prev_op[end]] == self.opc.POP_BLOCK
                         and code[self.prev_op[self.prev_op[end]]] == self.opc.RETURN_VALUE)):
                    jump_back = None
            if not jump_back: # loop suite ends in return. wtf right?
                jump_back = self.last_instr(start, end, self.opc.RETURN_VALUE) + 1
                if not jump_back:
                    return
                if code[self.prev_op[next_line_byte]] not in POP_JUMP_TF:
                    loop_type = 'for'
                else:
                    loop_type = 'while'
                    self.ignore_if.add(self.prev_op[next_line_byte])
                target = next_line_byte
                end = jump_back + 3
            else:
                if self.get_target(jump_back) >= next_line_byte:
                    jump_back = self.last_instr(start, end, self.opc.JUMP_ABSOLUTE, start, False)
                if end > jump_back+4 and self.is_jump_forward(end):
                    if self.is_jump_forward(jump_back+4):
                        if self.get_target(jump_back+4) == self.get_target(end):
                            self.fixed_jumps[offset] = jump_back+4
                            end = jump_back+4
                elif target < offset:
                    self.fixed_jumps[offset] = jump_back+4
                    end = jump_back+4
                target = self.get_target(jump_back)

                if code[target] in (self.opc.FOR_ITER, self.opc.GET_ITER):
                    loop_type = 'for'
                else:
                    loop_type = 'while'
                    test = self.prev_op[next_line_byte]
                    if test == offset:
                        loop_type = 'while 1'
                    elif self.code[test] in op3.hasjabs+op3.hasjrel:
                        self.ignore_if.add(test)
                        test_target = self.get_target(test)
                        if test_target > (jump_back+3):
                            jump_back = test_target
                self.not_continue.add(jump_back)
            self.loops.append(target)
            self.structs.append({'type': loop_type + '-loop',
                                   'start': target,
                                   'end':   jump_back})
            if jump_back+3 != end:
                self.structs.append({'type': loop_type + '-else',
                                       'start': jump_back+3,
                                       'end':   end})
        elif op in POP_JUMP_TF:
            start = offset + self.op_size(op)
            target = self.get_target(offset)
            rtarget = self.restrict_to_parent(target, parent)
            prev_op = self.prev_op

            # Do not let jump to go out of parent struct bounds
            if target != rtarget and parent['type'] == 'and/or':
                self.fixed_jumps[offset] = rtarget
                return

            # Does this jump to right after another conditional jump that is
            # not myself?  If so, it's part of a larger conditional.
            # rocky: if we have a conditional jump to the next instruction, then
            # possibly I am "skipping over" a "pass" or null statement.

            if ((code[prev_op[target]] in self.pop_jump_if_pop) and
                (target > offset) and prev_op[target] != offset):
                self.fixed_jumps[offset] = prev_op[target]
                self.structs.append({'type': 'and/or',
                                     'start': start,
                                     'end': prev_op[target]})
                return

            # Is it an "and" inside an "if" block
            if op == self.opc.POP_JUMP_IF_FALSE:
                # Search for another POP_JUMP_IF_FALSE targetting the same op,
                # in current statement, starting from current offset, and filter
                # everything inside inner 'or' jumps and midline ifs
                match = self.rem_or(start, self.next_stmt[offset],
                                    self.opc.POP_JUMP_IF_FALSE, target)
                ## We can't remove mid-line ifs because line structures have changed
                ## from restructBytecode().
                ##  match = self.remove_mid_line_ifs(match)

                # If we still have any offsets in set, start working on it
                if match:
                    is_jump_forward = self.is_jump_forward(prev_op[rtarget])
                    if (is_jump_forward and prev_op[rtarget] not in self.stmts and
                        self.restrict_to_parent(self.get_target(prev_op[rtarget]), parent) == rtarget):
                        if (code[prev_op[prev_op[rtarget]]] == self.opc.JUMP_ABSOLUTE
                            and self.remove_mid_line_ifs([offset]) and
                            target == self.get_target(prev_op[prev_op[rtarget]]) and
                            (prev_op[prev_op[rtarget]] not in self.stmts or
                             self.get_target(prev_op[prev_op[rtarget]]) > prev_op[prev_op[rtarget]]) and
                            1 == len(self.remove_mid_line_ifs(self.rem_or(start, prev_op[prev_op[rtarget]], POP_JUMP_TF, target)))):
                            pass
                        elif (code[prev_op[prev_op[rtarget]]] == self.opc.RETURN_VALUE
                              and self.remove_mid_line_ifs([offset]) and
                              1 == (len(set(self.remove_mid_line_ifs(self.rem_or(start, prev_op[prev_op[rtarget]],
                                                                                 POP_JUMP_TF, target))) |
                                    set(self.remove_mid_line_ifs(self.rem_or(start, prev_op[prev_op[rtarget]],
                                                                             (self.opc.POP_JUMP_IF_FALSE,
                                                                              self.opc.POP_JUMP_IF_TRUE,
                                                                              self.opc.JUMP_ABSOLUTE),
                                                                             prev_op[rtarget], True)))))):
                            pass
                        else:
                            fix = None
                            jump_ifs = self.all_instr(start, self.next_stmt[offset],
                                                      self.opc.POP_JUMP_IF_FALSE)
                            last_jump_good = True
                            for j in jump_ifs:
                                if target == self.get_target(j):
                                    if self.lines[j].next == j + 3 and last_jump_good:
                                        fix = j
                                        break
                                else:
                                    last_jump_good = False
                            self.fixed_jumps[offset] = fix or match[-1]
                            return
                    else:
                        if is_jump_forward:
                            self.fixed_jumps[offset] = match[-1]
                        return
            # op == POP_JUMP_IF_TRUE
            else:
                next = self.next_stmt[offset]
                if prev_op[next] == offset:
                    pass
                elif self.is_jump_forward(next) and target == self.get_target(next):
                    if code[prev_op[next]] == self.opc.POP_JUMP_IF_FALSE:
                        if (code[next] == self.opc.JUMP_FORWARD
                            or target != rtarget
                            or code[prev_op[prev_op[rtarget]]] not in
                            (self.opc.JUMP_ABSOLUTE, self.opc.RETURN_VALUE)):
                            self.fixed_jumps[offset] = prev_op[next]
                            return
                elif (code[next] == self.opc.JUMP_ABSOLUTE and self.is_jump_forward(target) and
                      self.get_target(target) == self.get_target(next)):
                    self.fixed_jumps[offset] = prev_op[next]
                    return

            # Don't add a struct for a while test, it's already taken care of
            if offset in self.ignore_if:
                return

            if (code[prev_op[rtarget]] == self.opc.JUMP_ABSOLUTE and
                prev_op[rtarget] in self.stmts and
                prev_op[rtarget] != offset and
                prev_op[prev_op[rtarget]] != offset and
                not (code[rtarget] == self.opc.JUMP_ABSOLUTE and
                     code[rtarget+3] == self.opc.POP_BLOCK and
                     code[prev_op[prev_op[rtarget]]] != self.opc.JUMP_ABSOLUTE)):
                rtarget = prev_op[rtarget]

            # Does the "if" jump just beyond a jump op, then this is probably an if statement
            if self.is_jump_forward(prev_op[rtarget]):
                if_end = self.get_target(prev_op[rtarget])

                # Is this a loop and not an "if" statement?
                if ((if_end < prev_op[rtarget]) and
                    (code[prev_op[if_end]] == self.opc.SETUP_LOOP)):
                    if(if_end > start):
                        return

                end = self.restrict_to_parent(if_end, parent)

                self.structs.append({'type': 'if-then',
                                     'start': start,
                                     'end': prev_op[rtarget]})
                self.not_continue.add(prev_op[rtarget])

                if rtarget < end:
                    self.structs.append({'type': 'if-else',
                                         'start': rtarget,
                                         'end': end})
            elif code[prev_op[rtarget]] == self.opc.RETURN_VALUE:
                self.structs.append({'type': 'if-then',
                                     'start': start,
                                     'end': rtarget})
                self.return_end_ifs.add(prev_op[rtarget])

        elif op in self.jump_if_pop:
            target = self.get_target(offset)
            if target > offset:
                unop_target = self.last_instr(offset, target, self.opc.JUMP_FORWARD, target)
                if unop_target and code[unop_target+3] != self.opc.ROT_TWO:
                    self.fixed_jumps[offset] = unop_target
                else:
                    self.fixed_jumps[offset] = self.restrict_to_parent(target, parent)


    def next_except_jump(self, start):
        """
        Return the next jump that was generated by an except SomeException:
        construct in a try...except...else clause or None if not found.
        """

        if self.code[start] == self.opc.DUP_TOP:
            except_match = self.first_instr(start, len(self.code), self.opc.POP_JUMP_IF_FALSE)
            if except_match:
                jmp = self.prev_op[self.get_target(except_match)]
                self.ignore_if.add(except_match)
                self.not_continue.add(jmp)
                return jmp

        count_END_FINALLY = 0
        count_SETUP_ = 0
        for i in self.op_range(start, len(self.code)):
            op = self.code[i]
            if op == self.opc.END_FINALLY:
                if count_END_FINALLY == count_SETUP_:
                    assert self.code[self.prev_op[i]] in (JUMP_ABSOLUTE, JUMP_FORWARD, RETURN_VALUE)
                    self.not_continue.add(self.prev_op[i])
                    return self.prev_op[i]
                count_END_FINALLY += 1
            elif op in (self.opc.SETUP_EXCEPT, self.opc.SETUP_WITH, self.opc.SETUP_FINALLY):
                count_SETUP_ += 1

    def rem_or(self, start, end, instr, target=None, include_beyond_target=False):
        """
        Find offsets of all requested <instr> between <start> and <end>,
        optionally <target>ing specified offset, and return list found
        <instr> offsets which are not within any POP_JUMP_IF_TRUE jumps.
        """
        assert(start>=0 and end<=len(self.code) and start <= end)

        # Find all offsets of requested instructions
        instr_offsets = self.all_instr(start, end, instr, target, include_beyond_target)
        # Get all POP_JUMP_IF_TRUE (or) offsets
        pjit_offsets = self.all_instr(start, end, self.opc.POP_JUMP_IF_TRUE)
        filtered = []
        for pjit_offset in pjit_offsets:
            pjit_tgt = self.get_target(pjit_offset) - 3
            for instr_offset in instr_offsets:
                if instr_offset <= pjit_offset or instr_offset >= pjit_tgt:
                    filtered.append(instr_offset)
            instr_offsets = filtered
            filtered = []
        return instr_offsets

if __name__ == "__main__":
    from uncompyle6 import PYTHON_VERSION
    if PYTHON_VERSION >= 3.2:
        import inspect
        co = inspect.currentframe().f_code
        from uncompyle6 import PYTHON_VERSION
        tokens, customize = Scanner3(PYTHON_VERSION).disassemble(co)
        for t in tokens:
            print(t.format())
    else:
        print("Need to be Python 3.2 or greater to demo; I am %s." %
              PYTHON_VERSION)
    pass
