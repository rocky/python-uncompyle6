#  Copyright (c) 2016, 2017 by Rocky Bernstein
"""
Python 3.0 bytecode scanner/deparser

This sets up opcodes Python's 3.0 and calls a generalized
scanner routine for Python 3.
"""

from __future__ import print_function

# bytecode verification, verify(), uses JUMP_OPs from here
from xdis.opcodes import opcode_30 as opc
from xdis.bytecode import instruction_size
import xdis

JUMP_TF = frozenset([opc.JUMP_IF_FALSE, opc.JUMP_IF_TRUE])

from uncompyle6.scanners.scanner3 import Scanner3
class Scanner30(Scanner3):

    def __init__(self, show_asm=None, is_pypy=False):
        Scanner3.__init__(self, 3.0, show_asm, is_pypy)
        return
    pass

    def detect_control_flow(self, offset, targets, inst_index):
        """
        Detect structures and their boundaries to fix optimized jumps
        Python 3.0 is more like Python 2.6 than it is Python 3.x.
        So we have a special routine here.
        """

        code = self.code
        op = self.insts[inst_index].opcode

        # Detect parent structure
        parent = self.structs[0]
        start  = parent['start']
        end    = parent['end']

        # Pick inner-most parent for our offset
        for struct in self.structs:
            current_start = struct['start']
            current_end   = struct['end']
            if ((current_start <= offset < current_end)
                and (current_start >= start and current_end <= end)):
                start  = current_start
                end    = current_end
                parent = struct

        if op == self.opc.SETUP_LOOP:
            # We categorize loop types: 'for', 'while', 'while 1' with
            # possibly suffixes '-loop' and '-else'
            # Try to find the jump_back instruction of the loop.
            # It could be a return instruction.

            start += instruction_size(op, self.opc)
            target = self.get_target(offset)
            end    = self.restrict_to_parent(target, parent)
            self.setup_loops[target] = offset

            if target != end:
                self.fixed_jumps[offset] = end

            (line_no, next_line_byte) = self.lines[offset]
            jump_back = self.last_instr(start, end, self.opc.JUMP_ABSOLUTE,
                                            next_line_byte, False)

            if jump_back:
                jump_forward_offset = xdis.next_offset(code[jump_back], self.opc, jump_back)
            else:
                jump_forward_offset = None

            return_val_offset1 = self.prev[self.prev[end]]

            if (jump_back and jump_back != self.prev_op[end]
                and self.is_jump_forward(jump_forward_offset)):
                if (code[self.prev_op[end]] == self.opc.RETURN_VALUE or
                    (code[self.prev_op[end]] == self.opc.POP_BLOCK
                     and code[return_val_offset1] == self.opc.RETURN_VALUE)):
                    jump_back = None
            if not jump_back:
                # loop suite ends in return
                jump_back = self.last_instr(start, end, self.opc.RETURN_VALUE)
                if not jump_back:
                    return

                jb_inst = self.get_inst(jump_back)
                jump_back = self.next_offset(jb_inst.opcode, jump_back)

                if_offset = None
                if code[self.prev_op[next_line_byte]] not in JUMP_TF:
                    if_offset = self.prev[next_line_byte]
                if if_offset:
                    loop_type = 'while'
                    self.ignore_if.add(if_offset)
                else:
                    loop_type = 'for'
                target = next_line_byte
                end = jump_back + 3
            else:
                if self.get_target(jump_back) >= next_line_byte:
                    jump_back = self.last_instr(start, end, self.opc.JUMP_ABSOLUTE, start, False)

                jb_inst = self.get_inst(jump_back)

                jb_next_offset = self.next_offset(jb_inst.opcode, jump_back)
                if end > jb_next_offset and self.is_jump_forward(end):
                    if self.is_jump_forward(jb_next_offset):
                        if self.get_target(jump_back+4) == self.get_target(end):
                            self.fixed_jumps[offset] = jump_back+4
                            end = jb_next_offset
                elif target < offset:
                    self.fixed_jumps[offset] = jump_back+4
                    end = jb_next_offset

                target = self.get_target(jump_back)

                if code[target] in (self.opc.FOR_ITER, self.opc.GET_ITER):
                    loop_type = 'for'
                else:
                    loop_type = 'while'
                    test = self.prev_op[next_line_byte]

                    if test == offset:
                        loop_type = 'while 1'
                    elif self.code[test] in self.opc.JUMP_OPs:
                        self.ignore_if.add(test)
                        test_target = self.get_target(test)
                        if test_target > (jump_back+3):
                            jump_back = test_target
                self.not_continue.add(jump_back)
            self.loops.append(target)
            self.structs.append({'type': loop_type + '-loop',
                                 'start': target,
                                 'end':   jump_back})
            after_jump_offset = xdis.next_offset(code[jump_back], self.opc, jump_back)
            if (self.get_inst(after_jump_offset).opname == 'POP_TOP'):
                after_jump_offset = xdis.next_offset(code[after_jump_offset], self.opc,
                                                     after_jump_offset)
            if after_jump_offset != end:
                self.structs.append({'type': loop_type + '-else',
                                     'start': after_jump_offset,
                                     'end':   end})
        elif op in self.pop_jump_tf:
            start = offset + instruction_size(op, self.opc)
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

            # The op offset just before the target jump offset is important
            # in making a determination of what we have. Save that.
            pre_rtarget = prev_op[rtarget]

            # Is it an "and" inside an "if" or "while" block
            if op == opc.JUMP_IF_FALSE:

                # Search for another JUMP_IF_FALSE targetting the same op,
                # in current statement, starting from current offset, and filter
                # everything inside inner 'or' jumps and midline ifs
                match = self.rem_or(start, self.next_stmt[offset],
                                    opc.JUMP_IF_FALSE, target)

                # If we still have any offsets in set, start working on it
                if match:
                    is_jump_forward = self.is_jump_forward(pre_rtarget)
                    if (is_jump_forward and pre_rtarget not in self.stmts and
                        self.restrict_to_parent(self.get_target(pre_rtarget), parent) == rtarget):
                        if (code[prev_op[pre_rtarget]] == self.opc.JUMP_ABSOLUTE
                            and self.remove_mid_line_ifs([offset]) and
                            target == self.get_target(prev_op[pre_rtarget]) and
                            (prev_op[pre_rtarget] not in self.stmts or
                             self.get_target(prev_op[pre_rtarget]) > prev_op[pre_rtarget]) and
                            1 == len(self.remove_mid_line_ifs(self.rem_or(start, prev_op[pre_rtarget], JUMP_TF, target)))):
                            pass
                        elif (code[prev_op[pre_rtarget]] == self.opc.RETURN_VALUE
                              and self.remove_mid_line_ifs([offset]) and
                              1 == (len(set(self.remove_mid_line_ifs(self.rem_or(start, prev_op[pre_rtarget],
                                                                                 JUMP_TF, target))) |
                                    set(self.remove_mid_line_ifs(self.rem_or(start, prev_op[pre_rtarget],
                                                                             (opc.JUMP_IF_FALSE,
                                                                              opc.JUMP_IF_TRUE,
                                                                              opc.JUMP_ABSOLUTE),
                                                                             pre_rtarget, True)))))):
                            pass
                        else:
                            fix = None
                            jump_ifs = self.inst_matches(start, self.next_stmt[offset],
                                                         opc.JUMP_IF_FALSE)
                            last_jump_good = True
                            for j in jump_ifs:
                                if target == self.get_target(j):
                                    # FIXME: remove magic number
                                    if self.lines[j].next == j + 3 and last_jump_good:
                                        fix = j
                                        break
                                else:
                                    last_jump_good = False
                            self.fixed_jumps[offset] = fix or match[-1]
                            return
                    else:
                        self.fixed_jumps[offset] = match[-1]
                        return
            # op == JUMP_IF_TRUE
            else:
                next = self.next_stmt[offset]
                if prev_op[next] == offset:
                    pass
                elif self.is_jump_forward(next) and target == self.get_target(next):
                    if code[prev_op[next]] == opc.JUMP_IF_FALSE:
                        if (code[next] == self.opc.JUMP_FORWARD
                            or target != rtarget
                            or code[prev_op[pre_rtarget]] not in
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

            if (code[pre_rtarget] == self.opc.JUMP_ABSOLUTE and
                pre_rtarget in self.stmts and
                pre_rtarget != offset and
                prev_op[pre_rtarget] != offset and
                not (code[rtarget] == self.opc.JUMP_ABSOLUTE and
                     code[rtarget+3] == self.opc.POP_BLOCK and
                     code[prev_op[pre_rtarget]] != self.opc.JUMP_ABSOLUTE)):
                rtarget = pre_rtarget

            # Does the "jump if" jump beyond a jump op?
            # That is, we have something like:
            #  JUMP_IF_FALSE HERE
            #  ...
            # JUMP_FORWARD
            # HERE:
            #
            # If so, this can be block inside an "if" statement
            # or a conditional assignment like:
            #   x = 1 if x else 2
            #
            # There are other contexts we may need to consider
            # like whether the target is "END_FINALLY"
            # or if the condition jump is to a forward location
            if self.is_jump_forward(pre_rtarget):
                if_end = self.get_target(pre_rtarget, 0)

                # If the jump target is back, we are looping
                if (if_end < pre_rtarget and
                    (code[prev_op[if_end]] == self.opc.SETUP_LOOP)):
                    if (if_end > start):
                        return

                end = self.restrict_to_parent(if_end, parent)

                self.structs.append({'type': 'if-then',
                                     'start': start,
                                     'end': pre_rtarget})
                self.not_continue.add(pre_rtarget)

                # if rtarget < end and (
                #         code[rtarget] not in (self.opc.END_FINALLY,
                #                               self.opc.JUMP_ABSOLUTE) and
                #         code[prev_op[pre_rtarget]] not in (self.opc.POP_EXCEPT,
                #                                         self.opc.END_FINALLY)):
                #     self.structs.append({'type': 'else',
                #                          'start': rtarget,
                #                          'end': end})
                #     self.else_start[rtarget] = end
            elif self.is_jump_back(pre_rtarget, 0):
                if_end = rtarget
                self.structs.append({'type': 'if-then',
                                     'start': start,
                                     'end': pre_rtarget})
                self.not_continue.add(pre_rtarget)
            elif code[pre_rtarget] in (self.opc.RETURN_VALUE,
                                       self.opc.BREAK_LOOP):
                self.structs.append({'type': 'if-then',
                                     'start': start,
                                     'end': rtarget})
                # It is important to distingish if this return is inside some sort
                # except block return
                jump_prev = prev_op[offset]
                if self.is_pypy and code[jump_prev] == self.opc.COMPARE_OP:
                    if self.opc.cmp_op[code[jump_prev+1]] == 'exception-match':
                        return
                if self.version >= 3.5:
                    # Python 3.5 may remove as dead code a JUMP
                    # instruction after a RETURN_VALUE. So we check
                    # based on seeing SETUP_EXCEPT various places.
                    if code[rtarget] == self.opc.SETUP_EXCEPT:
                        return
                    # Check that next instruction after pops and jump is
                    # not from SETUP_EXCEPT
                    next_op = rtarget
                    if code[next_op] == self.opc.POP_BLOCK:
                        next_op += instruction_size(self.code[next_op], self.opc)
                    if code[next_op] == self.opc.JUMP_ABSOLUTE:
                        next_op += instruction_size(self.code[next_op], self.opc)
                    if next_op in targets:
                        for try_op in targets[next_op]:
                            come_from_op = code[try_op]
                            if come_from_op == self.opc.SETUP_EXCEPT:
                                return
                            pass
                    pass
                if code[pre_rtarget] == self.opc.RETURN_VALUE:
                    if self.version == 3.0:
                        next_op = rtarget
                        if code[next_op] == self.opc.POP_TOP:
                            next_op = rtarget
                        for block in self.structs:
                            if block['type'] == 'while-loop' and block['end'] == next_op:
                                return
                        next_op += instruction_size(self.code[next_op], self.opc)
                        if code[next_op] == self.opc.POP_BLOCK:
                            return
                    self.return_end_ifs.add(pre_rtarget)
                else:
                    self.fixed_jumps[offset] = rtarget
                    self.not_continue.add(pre_rtarget)


        elif op == self.opc.SETUP_EXCEPT:
            target = self.get_target(offset)
            end    = self.restrict_to_parent(target, parent)
            self.fixed_jumps[offset] = end
        elif op == self.opc.SETUP_FINALLY:
            target = self.get_target(offset)
            end    = self.restrict_to_parent(target, parent)
            self.fixed_jumps[offset] = end
        elif op in self.jump_if_pop:
            target = self.get_target(offset)
            if target > offset:
                unop_target = self.last_instr(offset, target, self.opc.JUMP_FORWARD, target)
                if unop_target and code[unop_target+3] != self.opc.ROT_TWO:
                    self.fixed_jumps[offset] = unop_target
                else:
                    self.fixed_jumps[offset] = self.restrict_to_parent(target, parent)
                    pass
                pass
        elif self.version >= 3.5:
            # 3.5+ has Jump optimization which too often causes RETURN_VALUE to get
            # misclassified as RETURN_END_IF. Handle that here.
            # In RETURN_VALUE, JUMP_ABSOLUTE, RETURN_VALUE is never RETURN_END_IF
            if op == self.opc.RETURN_VALUE:
                if (offset+1 < len(code) and code[offset+1] == self.opc.JUMP_ABSOLUTE and
                    offset in self.return_end_ifs):
                    self.return_end_ifs.remove(offset)
                    pass
                pass
            elif op == self.opc.JUMP_FORWARD:
                # If we have:
                #   JUMP_FORWARD x, [non-jump, insns], RETURN_VALUE, x:
                # then RETURN_VALUE is not RETURN_END_IF
                rtarget = self.get_target(offset)
                rtarget_prev = self.prev[rtarget]
                if (code[rtarget_prev] == self.opc.RETURN_VALUE and
                    rtarget_prev in self.return_end_ifs):
                    i = rtarget_prev
                    while i != offset:
                        if code[i] in [opc.JUMP_FORWARD, opc.JUMP_ABSOLUTE]:
                            return
                        i = self.prev[i]
                    self.return_end_ifs.remove(rtarget_prev)
                pass
        return

if __name__ == "__main__":
    from uncompyle6 import PYTHON_VERSION
    if PYTHON_VERSION == 3.0:
        import inspect
        co = inspect.currentframe().f_code
        tokens, customize = Scanner30().ingest(co)
        for t in tokens:
            print(t)
        pass
    else:
        print("Need to be Python 3.0 to demo; I am %s." %
              PYTHON_VERSION)
