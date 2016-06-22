#  Copyright (c) 2015-2016 by Rocky Bernstein
#  Copyright (c) 2005 by Dan Pascu <dan@windowmaker.org>
#  Copyright (c) 2000-2002 by hartmut Goebel <h.goebel@crazy-compilers.com>
#  Copyright (c) 1999 John Aycock
"""
Python 2.5 bytecode scanner/deparser

This overlaps Python's 2.5's dis module, but it can be run from
Python 3 and other versions of Python. Also, we save token
information for later use in deparsing.
"""

from xdis.opcodes.opcode_25 import *
import uncompyle6.scanners.scanner26 as scan
import uncompyle6.scanners.scanner2 as scan2

# bytecode verification, verify(), uses JUMP_OPs from here
from xdis.opcodes import opcode_25
JUMP_OPs = opcode_25.JUMP_OPs

# We base this off of 2.6 instead of the other way around
# because we cleaned things up this way.
# The history is that 2.7 support is the cleanest,
# then from that we got 2.6 and so on.
class Scanner25(scan.Scanner26):
    def __init__(self, show_asm):
        scan2.Scanner2.__init__(self, 2.5, show_asm)
        self.stmt_opcodes = frozenset([
            self.opc.SETUP_LOOP,       self.opc.BREAK_LOOP,
            self.opc.SETUP_FINALLY,    self.opc.END_FINALLY,
            self.opc.SETUP_EXCEPT,     self.opc.POP_BLOCK,
            self.opc.STORE_FAST,       self.opc.DELETE_FAST,
            self.opc.STORE_DEREF,      self.opc.STORE_GLOBAL,
            self.opc.DELETE_GLOBAL,    self.opc.STORE_NAME,
            self.opc.DELETE_NAME,      self.opc.STORE_ATTR,
            self.opc.DELETE_ATTR,      self.opc.STORE_SUBSCR,
            self.opc.DELETE_SUBSCR,    self.opc.RETURN_VALUE,
            self.opc.RAISE_VARARGS,    self.opc.POP_TOP,
            self.opc.PRINT_EXPR,       self.opc.PRINT_ITEM,
            self.opc.PRINT_NEWLINE,    self.opc.PRINT_ITEM_TO,
            self.opc.PRINT_NEWLINE_TO, self.opc.CONTINUE_LOOP,
            self.opc.JUMP_ABSOLUTE,    self.opc.EXEC_STMT,
        ])

        # "setup" opcodes
        self.setup_ops = frozenset([
            self.opc.SETUP_EXCEPT, self.opc.SETUP_FINALLY,
            ])

        # opcodes with expect a variable number pushed values whose
        # count is in the opcode. For parsing we generally change the
        # opcode name to include that number.
        self.varargs_ops = frozenset([
            self.opc.BUILD_LIST,           self.opc.BUILD_TUPLE,
            self.opc.BUILD_SLICE,          self.opc.UNPACK_SEQUENCE,
            self.opc.MAKE_FUNCTION,        self.opc.CALL_FUNCTION,
            self.opc.MAKE_CLOSURE,         self.opc.CALL_FUNCTION_VAR,
            self.opc.CALL_FUNCTION_KW,     self.opc.CALL_FUNCTION_VAR_KW,
            self.opc.DUP_TOPX,             self.opc.RAISE_VARARGS])

        # opcodes that store values into a variable
        self.designator_ops = frozenset([
            self.opc.STORE_FAST,    self.opc.STORE_NAME,
            self.opc.STORE_GLOBAL,  self.opc.STORE_DEREF,   self.opc.STORE_ATTR,
            self.opc.STORE_SLICE_0, self.opc.STORE_SLICE_1, self.opc.STORE_SLICE_2,
            self.opc.STORE_SLICE_3, self.opc.STORE_SUBSCR,  self.opc.UNPACK_SEQUENCE,
            self.opc.JA
        ])
        # Python 2.7 has POP_JUMP_IF_{TRUE,FALSE}_OR_POP but < 2.7 doesn't
        # Add an empty set make processing more uniform.
        self.pop_jump_if_or_pop = frozenset([])
        return

    def restructCode(self, listDel, listExp):
        '''
        restruct linestarts and jump destination
        '''
        # restruct linestarts with deleted / modificated opcode
        result = list()
        for block in self.linestarts:
            startBlock = 0
            for toDel in listDel:
                if toDel < block[0]:
                    startBlock -= self.op_size(self.code[toDel])
            for toExp in listExp:
                if toExp < block[0]:
                    startBlock += 2
            result.append((block[0]+startBlock, block[1]))
        self.linestarts = result
        # handle opcodeToChange deplacement
        for index in range(len(self.toChange)):
            change = self.toChange[index]
            delta = 0
            for toDel in listDel:
                if change > toDel:
                    delta -= self.op_size(self.code[toDel])
            for toExp in listExp:
                if change > toExp:
                    delta += 2
            self.toChange[index] += delta
        # restruct jmp opcode
        if listDel:
            for jmp in self.op_range(0, len(self.code)):
                op = self.code[jmp]
                if op in self.opc.hasjrel + self.opc.hasjabs:
                    offset = 0
                    jmpTarget = self.get_target(jmp)
                    for toDel in listDel:
                        if toDel < jmpTarget:
                            if op in self.opc.hasjabs or jmp < toDel:
                                 offset-=self.op_size(self.code[toDel])
                    self.restructJump(jmp, jmpTarget+offset)
        if listExp:
            jmp = 0
            while jmp < len(self.code): # we can't use op_range for the moment
                op = self.code[jmp]
                if op in self.opc.hasjrel + self.opc.hasjabs:
                    offset = 0
                    jmpTarget = self.get_target(jmp)
                    for toExp in listExp:
                        if toExp < jmpTarget:
                            if op in self.opc.hasjabs or jmp < toExp:
                                offset+=2
                    self.restructJump(jmp, jmpTarget+offset)
                if self.op_hasArgument(op) and op not in self.opc.hasArgumentExtended:
                    jmp += 3
                else: jmp += 1

    def restructBytecode(self):
        '''
        add/change/delete bytecode for suiting bytecode 2.7
        '''
        # we can't use op_range for the moment
        # convert jump opcode to 2.7
        self.restructRelativeJump()

        listExp = self.getOpcodeToExp()
        # change code structure
        if listExp:
            listExp = sorted(list(set(listExp)))
            self.restructCode([], listExp)
            # we add arg to expended opcode
            offset=0
            for toExp in listExp:
                self.code.insert(toExp+offset+1, 0)
                self.code.insert(toExp+offset+1, 0)
                offset+=2
        # op_range is now ok :)
        # add instruction to change in "toChange" list + MAJ toDel
        listDel = []
        for i in self.op_range(0, len(self.code)):
            ret = self.getOpcodeToDel(i)
            if ret is not None:
                listDel += ret

        # change code structure after deleting byte
        if listDel:
            listDel = sorted(list(set(listDel)))
            self.restructCode(listDel, [])
            # finaly we delete useless opcode
            delta = 0
            for x in listDel:
                if self.op_hasArgument(self.code[x-delta]):
                    self.code.pop(x-delta)
                    self.code.pop(x-delta)
                    self.code.pop(x-delta)
                    delta += 3
                else:
                    self.code.pop(x-delta)
                    delta += 1

    def detect_structure(self, pos, op=None):
        '''
        Detect type of block structures and their boundaries to fix optimizied jumps
        in python2.3+
        '''

        code = self.code
        # Ev remove this test and make op a mandatory argument -Dan
        if op is None:
            op = code[pos]

        # Detect parent structure
        parent = self.structs[0]
        start  = parent['start']
        end    = parent['end']
        for s in self.structs:
            _start = s['start']
            _end   = s['end']
            if (_start <= pos < _end) and (_start >= start and _end <= end):
                start  = _start
                end    = _end
                parent = s
        # We need to know how many new structures were added in this run


        if op == self.opc.SETUP_LOOP:
            start = pos+3
            target = self.get_target(pos, op)
            end    = self.restrict_to_parent(target, parent)

            if target != end:
                self.fixed_jumps[pos] = end

            (line_no, next_line_byte) = self.lines[pos]
            jump_back = self.last_instr(start, end, self.opc.JA, next_line_byte, False)
            if jump_back and jump_back != self.prev[end] and code[jump_back+3] in (JA, JF):
                if code[self.prev[end]] == RETURN_VALUE or \
                    (code[self.prev[end]] == POP_BLOCK and code[self.prev[self.prev[end]]] == RETURN_VALUE):
                    jump_back = None
            if not jump_back: # loop suite ends in return. wtf right?
                jump_back = self.last_instr(start, end, RETURN_VALUE)
                if not jump_back:
                    return
                jump_back += 1
                if code[self.prev[next_line_byte]] not in self.pop_jump_if:
                    loop_type = 'for'
                else:
                    loop_type = 'while'
                    self.ignore_if.add(self.prev[next_line_byte])
                target = next_line_byte
                end = jump_back + 3
            else:
                if self.get_target(jump_back) >= next_line_byte:
                    jump_back = self.last_instr(start, end, JA,
                                              start, False)
                if end > jump_back+4 and code[end] in (JF, JA):
                    if code[jump_back+4] in (JA, JF):
                        if self.get_target(jump_back+4) == self.get_target(end):
                            self.fixed_jumps[pos] = jump_back+4
                            end = jump_back+4
                elif target < pos:
                    self.fixed_jumps[pos] = jump_back+4
                    end = jump_back+4

                target = self.get_target(jump_back, self.opc.JA)

                if code[target] in (self.opc.FOR_ITER, self.opc.GET_ITER):
                    loop_type = 'for'
                else:
                    loop_type = 'while'
                    test = self.prev[next_line_byte]
                    if test == pos:
                        loop_type = 'while 1'
                    elif self.code[test] in self.opc.hasjabs + self.opc.hasjrel:
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
        elif op == self.opc.SETUP_EXCEPT:
            start  = pos+3
            target = self.get_target(pos, op)
            end    = self.restrict_to_parent(target, parent)
            if target != end:
                self.fixed_jumps[pos] = end
            # Add the try block
            self.structs.append({'type':  'try',
                                   'start': start,
                                   'end':   end-4})
            #  Now isolate the except and else blocks
            end_else = start_else = self.get_target(self.prev[end])

            # Add the except blocks
            i = end
            while i < len(self.code) and self.code[i] != self.opc.END_FINALLY:
                 jmp = self.next_except_jump(i)
                 if jmp is None: # check
                    i = self.next_stmt[i]
                    continue
                 if self.code[jmp] == self.opc.RETURN_VALUE:
                     self.structs.append({'type':  'except',
                                           'start': i,
                                           'end':   jmp+1})
                     i = jmp + 1
                 else:
                    if self.get_target(jmp) != start_else:
                        end_else = self.get_target(jmp)
                    if self.code[jmp] == self.opc.JF:
                        self.fixed_jumps[jmp] = -1
                    self.structs.append({'type':  'except',
                                   'start': i,
                                   'end':   jmp})
                    i = jmp + 3

            # Add the try-else block
            if end_else != start_else:
                r_end_else = self.restrict_to_parent(end_else, parent)
                self.structs.append({'type':  'try-else',
                                       'start': i+2, # check
                                       'end':   r_end_else})
                self.fixed_jumps[i] = r_end_else
            else:
                self.fixed_jumps[i] = i+1

        elif op in self.pop_jump_if:
            start = pos+3
            target = self.get_target(pos, op)
            rtarget = self.restrict_to_parent(target, parent)
            pre = self.prev

            if target != rtarget and parent['type'] == 'and/or':
                self.fixed_jumps[pos] = rtarget
                return
            # does this jump to right after another cond jump?
            # if so, it's part of a larger conditional
            if (code[pre[target]] in (PJIF, PJIT)) and (target > pos):
                self.fixed_jumps[pos] = pre[target]
                self.structs.append({'type':  'and/or',
                                       'start': start,
                                       'end':   pre[target]})
                return

            # is this an if and
            if op == PJIF:
                match = self.rem_or(start, self.next_stmt[pos], PJIF, target)
                match = self.remove_mid_line_ifs(match)
                if match:
                    if code[pre[rtarget]] in (JF, JA) \
                            and pre[rtarget] not in self.stmts \
                            and self.restrict_to_parent(self.get_target(pre[rtarget]), parent) == rtarget:
                        if code[pre[pre[rtarget]]] == JA \
                                and self.remove_mid_line_ifs([pos]) \
                                and target == self.get_target(pre[pre[rtarget]]) \
                                and (pre[pre[rtarget]] not in self.stmts or self.get_target(pre[pre[rtarget]]) > pre[pre[rtarget]])\
                                and 1 == len(self.remove_mid_line_ifs(self.rem_or(start, pre[pre[rtarget]], (PJIF, PJIT), target))):
                            pass
                        elif code[pre[pre[rtarget]]] == RETURN_VALUE \
                                and self.remove_mid_line_ifs([pos]) \
                                and 1 == (len(set(self.remove_mid_line_ifs(self.rem_or(start, pre[pre[rtarget]],
                                                             (PJIF, PJIT), target)))
                                              | set(self.remove_mid_line_ifs(self.rem_or(start, pre[pre[rtarget]],
                                                           (PJIF, PJIT, JA), pre[rtarget], True))))):
                            pass
                        else:
                            fix = None
                            jump_ifs = self.all_instr(start, self.next_stmt[pos], PJIF)
                            last_jump_good = True
                            for j in jump_ifs:
                                if target == self.get_target(j):
                                    if self.lines[j].next == j+3 and last_jump_good:
                                        fix = j
                                        break
                                else:
                                    last_jump_good = False
                            self.fixed_jumps[pos] = fix or match[-1]
                            return
                    elif pos < rtarget and code[target] == self.opc.ROT_TWO:
                        self.fixed_jumps[pos] = target
                        return
                    else:
                        self.fixed_jumps[pos] = match[-1]
                        return
            else: # op == PJIT
                if (pos+3) in self.load_asserts:
                    if code[pre[rtarget]] == self.opc.RAISE_VARARGS:
                        return
                    self.load_asserts.remove(pos+3)

                next = self.next_stmt[pos]
                if pre[next] == pos:
                    pass
                elif code[next] in (JF, JA) and target == self.get_target(next):
                    if code[pre[next]] == PJIF:
                        if code[next] == JF or target != rtarget or code[pre[pre[rtarget]]] not in (JA, RETURN_VALUE):
                            self.fixed_jumps[pos] = pre[next]
                            return
                elif code[next] == JA and code[target] in (JA, JF) \
                      and self.get_target(target) == self.get_target(next):
                    self.fixed_jumps[pos] = pre[next]
                    return
            # don't add a struct for a while test, it's already taken care of
            if pos in self.ignore_if:
                return

            if code[pre[rtarget]] == JA and pre[rtarget] in self.stmts \
                    and pre[rtarget] != pos and pre[pre[rtarget]] != pos \
                    and not (code[rtarget] == JA and code[rtarget+3] == POP_BLOCK and code[pre[pre[rtarget]]] != JA):
                rtarget = pre[rtarget]
            # does the if jump just beyond a jump op, then this is probably an if statement
            if code[pre[rtarget]] in (JA, JF):
                if_end = self.get_target(pre[rtarget])

                # is this a loop not an if?
                if (if_end < pre[rtarget]) and (code[pre[if_end]] == self.opc.SETUP_LOOP):
                     if(if_end > start):
                        return

                end = self.restrict_to_parent(if_end, parent)

                self.structs.append({'type':  'if-then',
                                       'start': start,
                                       'end':   pre[rtarget]})
                self.not_continue.add(pre[rtarget])

                if rtarget < end:
                    self.structs.append({'type':  'if-else',
                                       'start': rtarget,
                                       'end':   end})
            elif code[pre[rtarget]] == self.opc.RETURN_VALUE:
                # if it's an old JUMP_IF_FALSE_OR_POP, JUMP_IF_TRUE_OR_POP (return 1<2<3 case)
                if pos < rtarget and code[rtarget] == self.opc.ROT_TWO:
                    return
                self.structs.append({'type':  'if-then',
                                       'start': start,
                                       'end':   rtarget})
                self.return_end_ifs.add(pre[rtarget])
                pass
            pass
        return
    pass
