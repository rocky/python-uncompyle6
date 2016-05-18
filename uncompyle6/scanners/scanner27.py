# Copyright (c) 2015, 2016 by Rocky Bernstein
# Copyright (c) 2005 by Dan Pascu <dan@windowmaker.org>
# Copyright (c) 2000-2002 by hartmut Goebel <h.goebel@crazy-compilers.com>
# Copyright (c) 1999 John Aycock
"""
Python 2.7 bytecode scanner/deparser

This overlaps Python's 2.7's dis module, but it can be run from
Python 3 and other versions of Python. Also, we save token information
for later use in deparsing.
"""


from __future__ import print_function

import dis, inspect
from collections import namedtuple
from array import array

from uncompyle6.code import iscode
from uncompyle6.opcodes.opcode_27 import * # NOQA
import uncompyle6.scanner as scan

class Scanner27(scan.Scanner):
    def __init__(self):
        scan.Scanner.__init__(self, 2.7)

    def disassemble(self, co, classname=None, code_objects={}):
        """
        Disassemble a Python 3 ode object, returning a list of 'Token'.
        Various tranformations are made to assist the deparsing grammar.
        For example:
           -  various types of LOAD_CONST's are categorized in terms of what they load
           -  COME_FROM instructions are added to assist parsing control structures
           -  MAKE_FUNCTION and FUNCTION_CALLS append the number of positional aruments
        The main part of this procedure is modelled after
        dis.disassemble().
        """

        # import dis; dis.disassemble(co) # DEBUG

        # Container for tokens
        tokens = []

        customize = {}
        Token = self.Token # shortcut

        n = self.setup_code(co)
        self.build_lines_data(co, n)
        self.build_prev_op(n)

        # self.lines contains (block,addrLastInstr)
        if classname:
            classname = '_' + classname.lstrip('_') + '__'

            def unmangle(name):
                if name.startswith(classname) and name[-2:] != '__':
                    return name[len(classname) - 2:]
                return name

            free = [ unmangle(name) for name in (co.co_cellvars + co.co_freevars) ]
            names = [ unmangle(name) for name in co.co_names ]
            varnames = [ unmangle(name) for name in co.co_varnames ]
        else:
            free = co.co_cellvars + co.co_freevars
            names = co.co_names
            varnames = co.co_varnames

        self.load_asserts = set()
        for i in self.op_range(0, n):
            if self.code[i] == PJIT and self.code[i+3] == LOAD_GLOBAL:
                if names[self.get_argument(i+3)] == 'AssertionError':
                    self.load_asserts.add(i+3)

        cf = self.find_jump_targets()
        # contains (code, [addrRefToCode])
        last_stmt = self.next_stmt[0]
        i = self.next_stmt[last_stmt]
        replace = {}
        while i < n-1:
            if self.lines[last_stmt].next > i:
                if self.code[last_stmt] == PRINT_ITEM:
                    if self.code[i] == PRINT_ITEM:
                        replace[i] = 'PRINT_ITEM_CONT'
                    elif self.code[i] == PRINT_NEWLINE:
                        replace[i] = 'PRINT_NEWLINE_CONT'
            last_stmt = i
            i = self.next_stmt[i]

        imports = self.all_instr(0, n, (IMPORT_NAME, IMPORT_FROM, IMPORT_STAR))
        if len(imports) > 1:
            last_import = imports[0]
            for i in imports[1:]:
                if self.lines[last_import].next > i:
                    if self.code[last_import] == IMPORT_NAME == self.code[i]:
                        replace[i] = 'IMPORT_NAME_CONT'
                last_import = i

        extended_arg = 0
        for offset in self.op_range(0, n):
            if offset in cf:
                k = 0
                for j in cf[offset]:
                    tokens.append(Token('COME_FROM', None, repr(j),
                                    offset="%s_%d" % (offset, k)))
                    k += 1

            op = self.code[offset]
            op_name = opname[op]

            oparg = None; pattr = None
            if op >= HAVE_ARGUMENT:
                oparg = self.get_argument(offset) + extended_arg
                extended_arg = 0
                if op == EXTENDED_ARG:
                    extended_arg = oparg * scan.L65536
                    continue
                if op in hasconst:
                    const = co.co_consts[oparg]
                    if iscode(const):
                        oparg = const
                        if const.co_name == '<lambda>':
                            assert op_name == 'LOAD_CONST'
                            op_name = 'LOAD_LAMBDA'
                        elif const.co_name == '<genexpr>':
                            op_name = 'LOAD_GENEXPR'
                        elif const.co_name == '<dictcomp>':
                            op_name = 'LOAD_DICTCOMP'
                        elif const.co_name == '<setcomp>':
                            op_name = 'LOAD_SETCOMP'
                        # verify() uses 'pattr' for comparison, since 'attr'
                        # now holds Code(const) and thus can not be used
                        # for comparison (todo: think about changing this)
                        # pattr = 'code_object @ 0x%x %s->%s' %\
                        # (id(const), const.co_filename, const.co_name)
                        pattr = '<code_object ' + const.co_name + '>'
                    else:
                        pattr = const
                elif op in hasname:
                    pattr = names[oparg]
                elif op in hasjrel:
                    pattr = repr(offset + 3 + oparg)
                elif op in hasjabs:
                    pattr = repr(oparg)
                elif op in haslocal:
                    pattr = varnames[oparg]
                elif op in hascompare:
                    pattr = cmp_op[oparg]
                elif op in hasfree:
                    pattr = free[oparg]

            if op in (BUILD_LIST, BUILD_TUPLE, BUILD_SET, BUILD_SLICE,
                            UNPACK_SEQUENCE,
                            MAKE_FUNCTION, CALL_FUNCTION, MAKE_CLOSURE,
                            CALL_FUNCTION_VAR, CALL_FUNCTION_KW,
                            CALL_FUNCTION_VAR_KW, DUP_TOPX, RAISE_VARARGS
                            ):
                # CE - Hack for >= 2.5
                #      Now all values loaded via LOAD_CLOSURE are packed into
                #      a tuple before calling MAKE_CLOSURE.
                if op == BUILD_TUPLE and \
                    self.code[self.prev[offset]] == LOAD_CLOSURE:
                    continue
                else:
                    op_name = '%s_%d' % (op_name, oparg)
                    if op != BUILD_SLICE:
                        customize[op_name] = oparg
            elif op == JA:
                target = self.get_target(offset)
                if target < offset:
                    if offset in self.stmts and self.code[offset+3] not in (END_FINALLY, POP_BLOCK) \
                     and offset not in self.not_continue:
                        op_name = 'CONTINUE'
                    else:
                        op_name = 'JUMP_BACK'

            elif op == LOAD_GLOBAL:
                if offset in self.load_asserts:
                    op_name = 'LOAD_ASSERT'
            elif op == RETURN_VALUE:
                if offset in self.return_end_ifs:
                    op_name = 'RETURN_END_IF'

            if offset in self.linestartoffsets:
                linestart = self.linestartoffsets[offset]
            else:
                linestart = None

            if offset not in replace:
                tokens.append(Token(op_name, oparg, pattr, offset, linestart))
            else:
                tokens.append(Token(replace[offset], oparg, pattr, offset, linestart))
        return tokens, customize

    def disassemble_native(self, co, classname=None, code_objects={}):
        """
        Like disassemble3 but doesn't try to adjust any opcodes.
        """

        # Container for tokens
        tokens = []

        customize = {}
        Token = self.Token # shortcut

        n = self.setup_code(co)
        self.build_lines_data(co, n)

        # self.lines contains (block,addrLastInstr)
        if classname:
            classname = '_' + classname.lstrip('_') + '__'

            def unmangle(name):
                if name.startswith(classname) and name[-2:] != '__':
                    return name[len(classname) - 2:]
                return name

            free = [ unmangle(name) for name in (co.co_cellvars + co.co_freevars) ]
            names = [ unmangle(name) for name in co.co_names ]
            varnames = [ unmangle(name) for name in co.co_varnames ]
        else:
            free = co.co_cellvars + co.co_freevars
            names = co.co_names
            varnames = co.co_varnames

        extended_arg = 0
        for offset in self.op_range(0, n):
            op = self.code[offset]
            op_name = opname[op]

            oparg = None; pattr = None
            if op >= HAVE_ARGUMENT:
                oparg = self.get_argument(offset) + extended_arg
                extended_arg = 0
                if op == EXTENDED_ARG:
                    extended_arg = oparg * scan.L65536
                    continue
                if op in hasconst:
                    pattr = co.co_consts[oparg]
                elif op in hasname:
                    pattr = names[oparg]
                elif op in hasjrel:
                    pattr = repr(offset + 3 + oparg)
                elif op in hasjabs:
                    pattr = repr(oparg)
                elif op in haslocal:
                    pattr = varnames[oparg]
                elif op in hascompare:
                    pattr = cmp_op[oparg]
                elif op in hasfree:
                    pattr = free[oparg]

            if offset in self.linestartoffsets:
                linestart = self.linestartoffsets[offset]
            else:
                linestart = None

            tokens.append(Token(op_name, oparg, pattr, offset, linestart))
            pass
        return tokens, customize

    def setup_code(self, co):
        """
        Creates Python-independent bytecode structure (byte array) in
        self.code and records previous instruction in self.prev
        The size of self.code is returned
        """
        self.code = array('B', co.co_code)

        n = -1
        for i in self.op_range(0, len(self.code)):
            if self.code[i] in (RETURN_VALUE, END_FINALLY):
                n = i + 1
                pass
            pass
        assert n > -1, "Didn't find RETURN_VALUE or END_FINALLY FINALLY"
        self.code = array('B', co.co_code[:n])

        return n

    def build_prev_op(self, n):
        self.prev = [0]
        # mapping addresses of instruction & argument
        for i in self.op_range(0, n):
            op = self.code[i]
            self.prev.append(i)
            if op >= HAVE_ARGUMENT:
                self.prev.append(i)
                self.prev.append(i)
                pass
            pass

    def build_lines_data(self, co, n):
        """
        Initializes self.lines and self.linesstartoffsets
        """
        self.lines = []
        linetuple = namedtuple('linetuple', ['l_no', 'next'])

        # linestarts is a tuple of (offset, line number).
        # Turn that in a has that we can index
        linestarts = list(dis.findlinestarts(co))
        self.linestartoffsets = {}
        for offset, lineno in linestarts:
            self.linestartoffsets[offset] = lineno

        j = 0
        (prev_start_byte, prev_line_no) = linestarts[0]
        for (start_byte, line_no) in linestarts[1:]:
            while j < start_byte:
                self.lines.append(linetuple(prev_line_no, start_byte))
                j += 1
            prev_line_no = start_byte
        while j < n:
            self.lines.append(linetuple(prev_line_no, n))
            j+=1
        return

    def build_stmt_indices(self):
        code = self.code
        start = 0
        end = len(code)

        stmt_opcodes = set([
            SETUP_LOOP, BREAK_LOOP, CONTINUE_LOOP,
            SETUP_FINALLY, END_FINALLY, SETUP_EXCEPT, SETUP_WITH,
            POP_BLOCK, STORE_FAST, DELETE_FAST, STORE_DEREF,
            STORE_GLOBAL, DELETE_GLOBAL, STORE_NAME, DELETE_NAME,
            STORE_ATTR, DELETE_ATTR, STORE_SUBSCR, DELETE_SUBSCR,
            RETURN_VALUE, RAISE_VARARGS, POP_TOP,
            PRINT_EXPR, PRINT_ITEM, PRINT_NEWLINE, PRINT_ITEM_TO, PRINT_NEWLINE_TO,
            STORE_SLICE_0, STORE_SLICE_1, STORE_SLICE_2, STORE_SLICE_3,
            DELETE_SLICE_0, DELETE_SLICE_1, DELETE_SLICE_2, DELETE_SLICE_3,
            JUMP_ABSOLUTE, EXEC_STMT,
        ])

        stmt_opcode_seqs = [(PJIF, JF), (PJIF, JA), (PJIT, JF), (PJIT, JA)]

        designator_ops = set([
            STORE_FAST, STORE_NAME, STORE_GLOBAL, STORE_DEREF, STORE_ATTR,
            STORE_SLICE_0, STORE_SLICE_1, STORE_SLICE_2, STORE_SLICE_3,
            STORE_SUBSCR, UNPACK_SEQUENCE, JA
        ])

        prelim = self.all_instr(start, end, stmt_opcodes)

        stmts = self.stmts = set(prelim)
        pass_stmts = set()
        for seq in stmt_opcode_seqs:
            for i in self.op_range(start, end-(len(seq)+1)):
                match = True
                for elem in seq:
                    if elem != code[i]:
                        match = False
                        break
                    i += self.op_size(code[i])

                if match:
                    i = self.prev[i]
                    stmts.add(i)
                    pass_stmts.add(i)

        if pass_stmts:
            stmt_list = list(stmts)
            stmt_list.sort()
        else:
            stmt_list = prelim
        last_stmt = -1
        self.next_stmt = []
        slist = self.next_stmt = []
        i = 0
        for s in stmt_list:
            if code[s] == JA and s not in pass_stmts:
                target = self.get_target(s)
                if target > s or self.lines[last_stmt].l_no == self.lines[s].l_no:
                    stmts.remove(s)
                    continue
                j = self.prev[s]
                while code[j] == JA:
                    j = self.prev[j]
                if code[j] == LIST_APPEND: # list comprehension
                    stmts.remove(s)
                    continue
            elif code[s] == POP_TOP and code[self.prev[s]] == ROT_TWO:
                stmts.remove(s)
                continue
            elif code[s] in designator_ops:
                j = self.prev[s]
                while code[j] in designator_ops:
                    j = self.prev[j]
                if code[j] == FOR_ITER:
                    stmts.remove(s)
                    continue
            last_stmt = s
            slist += [s] * (s-i)
            i = s
        slist += [end] * (end-len(slist))

    def next_except_jump(self, start):
        '''
        Return the next jump that was generated by an except SomeException:
        construct in a try...except...else clause or None if not found.
        '''

        if self.code[start] == DUP_TOP:
            except_match = self.first_instr(start, len(self.code), POP_JUMP_IF_FALSE)
            if except_match:
                jmp = self.prev[self.get_target(except_match)]
                self.ignore_if.add(except_match)
                self.not_continue.add(jmp)
                return jmp

        count_END_FINALLY = 0
        count_SETUP_ = 0
        for i in self.op_range(start, len(self.code)):
            op = self.code[i]
            if op == END_FINALLY:
                if count_END_FINALLY == count_SETUP_:
                    assert self.code[self.prev[i]] in (JA, JF, RETURN_VALUE)
                    self.not_continue.add(self.prev[i])
                    return self.prev[i]
                count_END_FINALLY += 1
            elif op in (SETUP_EXCEPT, SETUP_WITH, SETUP_FINALLY):
                count_SETUP_ += 1

    def detect_structure(self, pos, op=None):
        '''
        Detect type of block structures and their boundaries to fix optimized jumps
        in python2.3+
        '''

        # TODO: check the struct boundaries more precisely -Dan

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

        if op == SETUP_LOOP:
            start = pos+3
            target = self.get_target(pos, op)
            end    = self.restrict_to_parent(target, parent)

            if target != end:
                self.fixed_jumps[pos] = end
            (line_no, next_line_byte) = self.lines[pos]
            jump_back = self.last_instr(start, end, JA,
                                          next_line_byte, False)

            if jump_back and jump_back != self.prev[end] and code[jump_back+3] in (JA, JF):
                if code[self.prev[end]] == RETURN_VALUE or \
                    (code[self.prev[end]] == POP_BLOCK and code[self.prev[self.prev[end]]] == RETURN_VALUE):
                    jump_back = None
            if not jump_back: # loop suite ends in return. wtf right?
                jump_back = self.last_instr(start, end, RETURN_VALUE) + 1
                if not jump_back:
                    return
                if code[self.prev[next_line_byte]] not in (PJIF, PJIT):
                    loop_type = 'for'
                else:
                    loop_type = 'while'
                    self.ignore_if.add(self.prev[next_line_byte])
                target = next_line_byte
                end = jump_back + 3
            else:
                if self.get_target(jump_back) >= next_line_byte:
                    jump_back = self.last_instr(start, end, JA, start, False)
                if end > jump_back+4 and code[end] in (JF, JA):
                    if code[jump_back+4] in (JA, JF):
                        if self.get_target(jump_back+4) == self.get_target(end):
                            self.fixed_jumps[pos] = jump_back+4
                            end = jump_back+4
                elif target < pos:
                    self.fixed_jumps[pos] = jump_back+4
                    end = jump_back+4
                target = self.get_target(jump_back, JA)

                if code[target] in (FOR_ITER, GET_ITER):
                    loop_type = 'for'
                else:
                    loop_type = 'while'
                    test = self.prev[next_line_byte]
                    if test == pos:
                        loop_type = 'while 1'
                    elif self.code[test] in hasjabs+hasjrel:
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
        elif op == SETUP_EXCEPT:
            start  = pos+3
            target = self.get_target(pos, op)
            end    = self.restrict_to_parent(target, parent)
            if target != end:
                self.fixed_jumps[pos] = end
                # print target, end, parent
            # Add the try block
            self.structs.append({'type':  'try',
                                   'start': start,
                                   'end':   end-4})
            # Now isolate the except and else blocks
            end_else = start_else = self.get_target(self.prev[end])

            # Add the except blocks
            i = end
            while self.code[i] != END_FINALLY:
                jmp = self.next_except_jump(i)
                if self.code[jmp] == RETURN_VALUE:
                    self.structs.append({'type':  'except',
                                           'start': i,
                                           'end':   jmp+1})
                    i = jmp + 1
                else:
                    if self.get_target(jmp) != start_else:
                        end_else = self.get_target(jmp)
                    if self.code[jmp] == JF:
                        self.fixed_jumps[jmp] = -1
                    self.structs.append({'type':  'except',
                                   'start': i,
                                   'end':   jmp})
                    i = jmp + 3

            # Add the try-else block
            if end_else != start_else:
                r_end_else = self.restrict_to_parent(end_else, parent)
                self.structs.append({'type':  'try-else',
                                       'start': i+1,
                                       'end':   r_end_else})
                self.fixed_jumps[i] = r_end_else
            else:
                self.fixed_jumps[i] = i+1

        elif op in (PJIF, PJIT):
            start = pos+3
            target = self.get_target(pos, op)
            rtarget = self.restrict_to_parent(target, parent)
            pre = self.prev

            if target != rtarget and parent['type'] == 'and/or':
                self.fixed_jumps[pos] = rtarget
                return
            # does this jump to right after another cond jump?
            # if so, it's part of a larger conditional
            if (code[pre[target]] in (JUMP_IF_FALSE_OR_POP, JUMP_IF_TRUE_OR_POP,
                    PJIF, PJIT)) and (target > pos):
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
                                and 1 == (len(set(self.remove_mid_line_ifs(self.rem_or(start,
                                                                                       pre[pre[rtarget]],
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
                    else:
                        self.fixed_jumps[pos] = match[-1]
                        return
            else: # op == PJIT
                if (pos+3) in self.load_asserts:
                    if code[pre[rtarget]] == RAISE_VARARGS:
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
                elif code[next] == JA and code[target] in (JA, JF):
                    next_target = self.get_target(next)
                    if self.get_target(target) == next_target:
                        self.fixed_jumps[pos] = pre[next]
                        return
                    elif code[next_target] in (JA, JF) and self.get_target(next_target) == self.get_target(target):
                        self.fixed_jumps[pos] = pre[next]
                        return

            # don't add a struct for a while test, it's already taken care of
            if pos in self.ignore_if:
                return

            if code[pre[rtarget]] == JA and pre[rtarget] in self.stmts \
                    and pre[rtarget] != pos and pre[pre[rtarget]] != pos:
                if code[rtarget] == JA and code[rtarget+3] == POP_BLOCK:
                    if code[pre[pre[rtarget]]] != JA:
                        pass
                    elif self.get_target(pre[pre[rtarget]]) != target:
                        pass
                    else:
                        rtarget = pre[rtarget]
                else:
                    rtarget = pre[rtarget]
            # does the if jump just beyond a jump op, then this is probably an if statement
            if code[pre[rtarget]] in (JA, JF):
                if_end = self.get_target(pre[rtarget])

                # is this a loop not an if?
                if (if_end < pre[rtarget]) and (code[pre[if_end]] == SETUP_LOOP):
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
            elif code[pre[rtarget]] == RETURN_VALUE:
                self.structs.append({'type':  'if-then',
                                       'start': start,
                                       'end':   rtarget})
                self.return_end_ifs.add(pre[rtarget])

        elif op in (JUMP_IF_FALSE_OR_POP, JUMP_IF_TRUE_OR_POP):
            target = self.get_target(pos, op)
            self.fixed_jumps[pos] = self.restrict_to_parent(target, parent)

    def find_jump_targets(self):
        '''
        Detect all offsets in a byte code which are jump targets.

        Return the list of offsets.

        This procedure is modelled after dis.findlabels(), but here
        for each target the number of jumps are counted.
        '''

        n = len(self.code)
        self.structs = [{'type':  'root',
                           'start': 0,
                           'end':   n-1}]
        self.loops = []  # All loop entry points
        self.fixed_jumps = {} # Map fixed jumps to their real destination
        self.ignore_if = set()
        self.build_stmt_indices()

        # Containers filled by detect_structure()
        self.not_continue = set()
        self.return_end_ifs = set()

        targets = {}
        for i in self.op_range(0, n):
            op = self.code[i]

            # Determine structures and fix jumps in Python versions
            # since 2.3
            self.detect_structure(i, op)

            if op >= HAVE_ARGUMENT:
                label = self.fixed_jumps.get(i)
                oparg = self.code[i+1] + self.code[i+2] * 256
                if label is None:
                    if op in hasjrel and op != FOR_ITER:
                        label = i + 3 + oparg
                    elif op in hasjabs:
                        if op in (JUMP_IF_FALSE_OR_POP, JUMP_IF_TRUE_OR_POP):
                            if (oparg > i):
                                label = oparg

                if label is not None and label != -1:
                    targets[label] = targets.get(label, []) + [i]
            elif op == END_FINALLY and i in self.fixed_jumps:
                label = self.fixed_jumps[i]
                targets[label] = targets.get(label, []) + [i]
        return targets

if __name__ == "__main__":
    co = inspect.currentframe().f_code
    tokens, customize = Scanner27().disassemble(co)
    for t in tokens:
        print(t)
    pass
