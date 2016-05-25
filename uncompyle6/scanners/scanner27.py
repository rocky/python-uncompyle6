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
        self.showast = False

    def disassemble(self, co, classname=None, code_objects={}, showast=False):
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
        self.showast = showast
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

        if self.showast:
            print('\n--- Original code modification during disassembly: ---\n')

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
                if target <= offset:
                    if (offset in self.stmts and self.code[offset+3] not in (END_FINALLY, POP_BLOCK) \
                        and offset not in self.not_continue) or offset in self.continue_oneline:
                        #0 JUMP_ABSOLUTE ---^
                        #1 NOT END_FINALLY, POP_BLOCK
                        if self.showast: print('%d %s --> CONTINUE' % (offset, op_name))
                        op_name = 'CONTINUE'
                    elif offset in self.JA_to_shortJF:
                        #0 JUMP_ABSOLUTE --+
                        #1 XXX          <--+
                        if self.showast: print('%d %s --> short JUMP_FORWARD' % (offset, op_name))
                        op_name = 'JUMP_FORWARD'
                        oparg = 0
                        pattr = repr(offset + 3 + oparg)
                    else:
                        #0 JUMP_ABSOLUTE ---^
                        if self.showast: print('%d %s --> JUMP_BACK' % (offset, op_name))
                        op_name = 'JUMP_BACK'
                elif offset in self.JA_to_RV:
                    #0 COMPARE_OP
                    #1 JUMP_ABSOLUTE/FORWARD --> RETURN_VEALUE
                    if self.showast: print('%d %s --> RETURN_VALUE' % (offset, op_name))
                    op_name = 'RETURN_VALUE'
                    oparg = None; pattr = None

            elif op == LOAD_GLOBAL:
                if offset in self.load_asserts:
                    if self.showast: print('%d %s --> LOAD_ASSERT' % (offset, op_name))
                    op_name = 'LOAD_ASSERT'
            elif op == RETURN_VALUE:
                if offset in self.return_end_ifs:
                    if self.showast: print('%d %s --> RETURN_END_IF' % (offset, op_name))
                    op_name = 'RETURN_END_IF'
                elif offset in self.return_end_ifs_rep_to_JF:
                    if self.showast: print('%d %s --> JUMP_FORWARD' % (offset, op_name))
                    op_name = 'JUMP_FORWARD'
                    pattr = self.JF_links[offset]

            if offset in self.linestartoffsets:
                linestart = self.linestartoffsets[offset]
            else:
                linestart = None

            if offset not in replace:
                tokens.append(Token(op_name, oparg, pattr, offset, linestart))
            else:
                tokens.append(Token(replace[offset], oparg, pattr, offset, linestart))
            
            if offset in self.add_additional_PB:
                if self.showast: print('%d %s + POP_BLOCK' % (offset, op_name))
                tokens.append(Token('POP_BLOCK', None, None, offset="%s_1" % offset))
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
        
        self.stmts_full = set(prelim)
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
        
        if self.showast:
            print('\n--- Build stmts list: ---\n')
        
        i = 0 
        for index, s in enumerate(stmt_list):
            if code[s] == JA and s not in pass_stmts:
                #JUMP_ABSOLUTE (s)
                target = self.get_target(s)
                if target > s or self.lines[last_stmt].l_no == self.lines[s].l_no:
                    #...                             0 last_stmt...
                    #JUMP_ABSOLUTE (s)  ---+  or       JUMP_ABSOLUTE (s)
                    #target...         <---+
                    stmts.remove(s)
                    if self.showast: print('%s %s (removed)' % (s, opname[code[s]]))
                    continue
                j = self.prev[s]
                while code[j] == JA:
                    j = self.prev[j]
                if code[j] == LIST_APPEND: # list comprehension
                    stmts.remove(s)
                    if self.showast: print('%s %s (removed)' % (s, opname[code[s]]))
                    continue
            elif code[s] == POP_TOP and code[self.prev[s]] == ROT_TWO:
                stmts.remove(s)
                if self.showast: print('%s %s (removed)' % (s, opname[code[s]]))
                continue
            elif code[s] in designator_ops:
                j = self.prev[s]
                while code[j] in designator_ops:
                    j = self.prev[j]
                if code[j] == FOR_ITER:
                    stmts.remove(s)
                    if self.showast: print('%s %s (removed)' % (s, opname[code[s]]))
                    continue
            if self.showast: print('%s %s' % (s, opname[code[s]]))
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
        pre = self.prev
        
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
            #_start...
            #pos
            #_end
            if (_start <= pos < _end) and (start <= _start and _end <= end):
                start  = _start
                end    = _end
                parent = s

        if op == SETUP_LOOP:
            #0 SETUP_LOOP     --+
            #    start          |
            #1   ...            |
            #    POP_BLOCK      | 
            #    ...            |
            #X target (~end) <--+
            start = pos+3
            target = self.get_target(pos, op) #link for loop-end
            end    = self.restrict_to_parent(target, parent) #return target or parent['end']

            if target != end:
                #0 SETUP_LOOP  ---^
                #...
                #end  <-- add COME_FROM 0
                if self.showast: print('###1')
                self.fixed_jumps[pos] = end #COME_FROM
            (line_no, next_line_byte) = self.lines[pos] #first inst of loop-body
            #0 SETUP_LOOP (line_no)
            #    start...
            #    POP_JUMP_IF_FALSE/TRUE
            #1   (next_line_byte)               <~~+ nearest!
            #    ...                               |
            #    JUMP_ABSOLUTE (last! jump_back) --+ 
            #    ...
            #X end
            jump_back = self.last_instr(start, end, JA, next_line_byte, False)

            if jump_back and jump_back != pre[end] and code[jump_back+3] in (JA, JF):
                #    jump_back ---^
                #    JUMP_ABSOLUTE/FORWARD
                #    ...
                #X end
                if self.showast: print('###2')
                if code[pre[end]] == RETURN_VALUE or \
                   (code[pre[end]] == POP_BLOCK and code[pre[pre[end]]] == RETURN_VALUE): 
                    #    ...          <RETURN_VALUE>
                    #    RETURN_VALUE <POP_BLOCK>
                    #X end
                    if self.showast: print('###3')
                    jump_back = None
            if not jump_back: # loop suite ends in return. wtf right?
                jump_back = self.last_instr(start, end, RETURN_VALUE) + 1
                if not jump_back:
                    #...
                    #X end
                    if self.showast: print('###4')
                    return
                #    RETURN_VALUE
                #    jump_back...
                #X end
                if code[pre[next_line_byte]] not in (PJIF, PJIT):
                    if self.showast: print('###5')
                    if pre[next_line_byte] == pos:
                        #0 SETUP_LOOP
                        #1   start (next_line_byte)
                        if self.showast: print('###6') 
                        loop_type = 'while 1'
                        if code[target] == POP_BLOCK and code[pre[target]] == RETURN_VALUE: #Python 2.7.1
                            #0 SETUP_LOOP              --+
                            #    ...                     |
                            #    RETURN_VALUE            |
                            #    POP_BLOCK (target)   <--+
                            if self.showast: print('###6_1')
                            self.add_additional_PB.add(pre[target])
                        elif code[jump_back] != POP_BLOCK and code[pre[target]] != POP_BLOCK: #Python 2.7.1
                            #0 SETUP_LOOP            --+
                            #    ...                   |
                            #    RETURN_VALUE          |
                            #    ...(jump_back)        |
                            #    ...target          <--+
                            if self.showast: print('###6_2')
                            self.add_additional_PB.add(pre[jump_back])
                    else:
                        #0 SETUP_LOOP
                        #    start...
                        #1   (next_line_byte)
                        if self.showast: print('###7')
                        loop_type = 'for'
                else:
                    #    POP_JUMP_IF_FALSE/TRUE
                    #1   (next_line_byte)
                    if self.showast: print('###8')
                    loop_type = 'while'
                    self.ignore_if.add(pre[next_line_byte])
                    self.ignore_if_SL.add(pre[next_line_byte])
                #1   target (next_line_byte)
                #    ...
                #    RETURN_VALUE
                #    jump_back  ---^
                #    end
                #    ...
                target = next_line_byte
                end = jump_back + 3
            else:
                if self.get_target(jump_back) >= next_line_byte:
                    #    start...                       <~~+ nearest!
                    #    ...                               |
                    #    JUMP_ABSOLUTE (last! jump_back) --+ 
                    #    ...
                    #X end
                    if self.showast: print('###9')
                    jump_back = self.last_instr(start, end, JA, start, False) #find last JB
                if end > jump_back+4 and code[end] in (JF, JA): #+1 is a POP_BLOCK
                    #    jump_back ---^
                    #    POP_BLOCK 
                    #    ...
                    #X end JUMP_ABSOLUTE/FORWARD
                    if self.showast: print('###10')
                    if code[jump_back+4] in (JA, JF):
                        #    POP_BLOCK 
                        #    JUMP_ABSOLUTE/FORWARD (jump_back+4)
                        #    ...
                        if self.showast: print('###11')
                        if self.get_target(jump_back+4) == self.get_target(end):
                            #    POP_BLOCK 
                            #    JUMP_ABSOLUTE/FORWARD   ---> A <-- add COME_FROM 0, 'end' move here
                            #    ...
                            #X end JUMP_ABSOLUTE/FORWARD ---> A
                            if self.showast: print('###12')
                            self.fixed_jumps[pos] = jump_back+4 #COME_FROM
                            end = jump_back+4
                elif target < pos:
                    #0 SETUP_LOOP  ---^
                    #    ...
                    #    jump_back ---^
                    #    POP_BLOCK 
                    #    (jump_back+4)  <-- add COME_FROM 0, 'end' move here
                    #    ...
                    #X end
                    if self.showast: print('###13')
                    self.fixed_jumps[pos] = jump_back+4
                    end = jump_back+4
                #    target    <--+
                #    ...          |
                #    jump_back ---+
                target = self.get_target(jump_back, JA)

                if code[target] in (FOR_ITER, GET_ITER):
                    #    GET_ITER          <~~+
                    #    FOR_ITER (target) <~~+
                    #    ...                  |
                    #    jump_back         ---+
                    if self.showast: print('###14')
                    loop_type = 'for'
                    if self.lines[target].l_no == self.lines[jump_back].l_no: #one line 
                        test = self.get_target(pre[jump_back])
                        if test == target:
                            #    JUMP_ABSOLUTE ---+   <--- Add CONTINUE
                            #    jump_back     ---+
                            if self.showast: print('###14_1')
                            self.continue_oneline.add(pre[jump_back])
                else:
                    loop_type = 'while'
                    test = pre[next_line_byte]
                    if self.next_stmt[pos] >= test: #not one line
                        if self.showast: print('###15')
                        if test == pos:
                            #0 SETUP_LOOP (test)
                            #1   (next_line_byte) 
                            loop_type = 'while 1'
                            test_target = self.get_target(test)
                            test = pre[test_target]
                            if self.showast: print('###16')
                            if code[test_target] == POP_BLOCK and code[test] == JA: #Python 2.7.1
                                #0 SETUP_LOOP                 --+
                                #    ...                        |
                                #    JUMP_ABSOLUTE (test)       |
                                #    POP_BLOCK (test_target) <--+
                                if self.showast: print('###17')
                                self.add_additional_PB.add(test)
                            elif code[jump_back+3] != POP_BLOCK and code[pre[test_target]] != POP_BLOCK: #Python 2.7.1
                                #0 SETUP_LOOP                 --+
                                #    ...                        |
                                #    JUMP_ABSOLUTE (jump_back)  |
                                #    ...                        |
                                #    test_target             <--+
                                if self.showast: print('###17_1')
                                self.add_additional_PB.add(jump_back)
                        elif code[test] in hasjabs+hasjrel:
                            #    POP_JUMP_IF_FALSE/TRUE/JF/JA... (test)
                            #1   (next_line_byte) 
                            if self.showast: print('###18')
                            self.ignore_if.add(test)
                            self.ignore_if_SL.add(test)
                            test_target = self.get_target(test)
                            if test_target > (jump_back+3):
                                if self.showast: print('###19')
                                jump_back = test_target
                    else: #one line
                        test = self.next_stmt[pos]
                        if jump_back < test:
                            test = jump_back
                        test = self.last_instr(start, test, (PJIF, PJIT))
                        if not test:
                            #0 SETUP_LOOP --->
                            #    start 
                            if self.showast: print('###20')
                            loop_type = 'while 1'
                            test = pre[jump_back]
                            if test == start and code[test] == JA:
                                #0 SETUP_LOOP --->
                                #    JUMP_ABSOLUTE (start, test)             <--- Add CONTINUE
                                #    JUMP_ABSOLUTE (jump_back)
                                if self.showast: print('###21')
                                self.continue_oneline.add(test)
                            test_target = self.get_target(pre[start])
                            test = pre[test_target]
                            if code[test_target] == POP_BLOCK and code[test] == JA: #Python 2.7.1
                                #0 SETUP_LOOP                 --+
                                #    ...                        |
                                #    JUMP_ABSOLUTE (test)       |
                                #    POP_BLOCK (test_target) <--+
                                if self.showast: print('###22')
                                self.add_additional_PB.add(test)
                            elif code[jump_back+3] != POP_BLOCK and code[pre[test_target]] != POP_BLOCK: #Python 2.7.1
                                #0 SETUP_LOOP                 --+
                                #    ...                        |
                                #    JUMP_ABSOLUTE (jump_back)  |
                                #    ...                        |
                                #    test_target             <--+
                                if self.showast: print('###22_1')
                                self.add_additional_PB.add(jump_back)
                        else:
                            #    POP_JUMP_IF_FALSE/TRUE/JF/JA... (test)
                            #    ...
                            if self.showast: print('###23')
                            self.ignore_if.add(test)
                            self.ignore_if_SL.add(test)
                            if code[pre[jump_back]] == JA and pre[pre[jump_back]] == test and code[self.get_target(test)] == POP_BLOCK:
                                #    POP_JUMP_IF_FALSE/TRUE (test)  -+
                                #    JUMP_ABSOLUTE                   |    <--- Add CONTINUE
                                #    JUMP_ABSOLUTE (jump_back) |
                                #    POP_BLOCK                    <--+
                                if self.showast: print('###24')
                                self.continue_oneline.add(pre[jump_back])
                            test_target = self.get_target(test)
                            if test_target > (jump_back+3):
                                if self.showast: print('###25')
                                jump_back = test_target
                self.not_continue.add(jump_back)
            self.loops.append(target)
            self.structs.append({'type': loop_type + '-loop',
                                   'start': target,
                                   'end':   jump_back})
            if jump_back+3 != end:
                #    jump_back
                #    ...
                #X end
                self.structs.append({'type': loop_type + '-else',
                                       'start': jump_back+3,
                                       'end':   end})
        elif op == SETUP_EXCEPT:
            #0 SETUP_EXCEPT         ------+
            #    start                    |
            #1   ...                      |
            #    POP_BLOCK                | 
            #    JUMP_FORWARD      --+    |
            #X POP_TOP target (~end) | <--+
            #  POP_TOP               |
            #  POP_TOP               |
            #  ...                   |
            #  JUMP_FORWARD   --+    |
            #    END_FINALLY    |    |
            #Y   ...            | <--+ 
            #    POP_BLOCK   <--+
            start  = pos+3
            target = self.get_target(pos, op) #link for try-end
            end    = self.restrict_to_parent(target, parent) #return target or parent['end']

            if target != end:
                #0 SETUP_EXCEPT  ---^
                #...
                #end  <-- add COME_FROM 0
                self.fixed_jumps[pos] = end #COME_FROM 0
            # Add the try block
            self.structs.append({'type':  'try',
                                 'start': start,
                                 'end':   end-4}) #POP_BLOCK
            # Now isolate the except and else blocks
            end_else = start_else = self.get_target(pre[end])

            # Add the except blocks
            i = end
            while code[i] != END_FINALLY:
                jmp = self.next_except_jump(i)
                if code[jmp] == RETURN_VALUE:
                    self.structs.append({'type':  'except',
                                           'start': i,
                                           'end':   jmp+1})
                    i = jmp + 1
                else:
                    if self.get_target(jmp) != start_else:
                        end_else = self.get_target(jmp)
                    if code[jmp] == JF:
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
            #0 COMPARE_OP
            #  POP_JUMP_IF_FALSE/TRUE --+
            #1   start                  |
            #    ...                    |
            #    JUMP_FORWARD    --+    |
            #X   target (~rtarget) | <--+
            #Y   ...            <--+
            start = pos+3 #first inst after "if"
            target = self.get_target(pos, op) #"else" first inst
            rtarget = self.restrict_to_parent(target, parent) #"end" of if-else-stucture

            if target != rtarget and parent['type'] == 'and/or':
                #POP_JUMP_IF_FALSE (and/or)   --+
                #  ...                          |
                #  POP_JUMP_IF_TRUE (op) --+    |
                #rtarget                   | <--+  Add COME_FROM
                #...                       |
                #target                 <--+
                if self.showast: print('@@@1')
                self.fixed_jumps[pos] = rtarget
                return

            # does this jump to right after another cond jump?
            # if so, it's part of a larger conditional
            if (code[pre[target]] in (JUMP_IF_FALSE_OR_POP, JUMP_IF_TRUE_OR_POP, PJIF, PJIT)) and (target > pos):
                #POP_JUMP_IF_FALSE (op)       --+
                #  ...                          |
                #  POP_JUMP_IF_TRUE/FALSE/...   |  Add COME_FROM
                #target                      <--+  
                self.fixed_jumps[pos] = pre[target]
                self.structs.append({'type':  'and/or',
                                     'start': start,
                                     'end':   pre[target]})
                if self.showast: print('@@@2')
                return

            # is this an if and
            if op == PJIF:
                match = self.rem_or(start, self.next_stmt[pos], PJIF, target, False, False) #search all next PJIF's with same target
                match = self.remove_mid_line_ifs(match) #return last if
                if self.showast: print('@@@3')
                if match:
                    #0 POP_JUMP_IF_FALSE ---> target
                    #     ...
                    #     POP_JUMP_IF_FALSE (match) ---> target
                    #1 ...
                    if self.showast: print('@@@4')
                    if code[pre[rtarget]] in (JF, JA) \
                            and pre[rtarget] not in self.stmts \
                            and self.restrict_to_parent(self.get_target(pre[rtarget]), parent) == rtarget:
                        #1   ...             ^
                        #    ...             |
                        #    JUMP_FORWARD/A  +--->
                        #    ...         <---+
                        #X   rtarget
                        if self.showast: print('@@@5')
                        if code[pre[pre[rtarget]]] == JA \
                                and self.remove_mid_line_ifs([pos]) \
                                and target == self.get_target(pre[pre[rtarget]]) \
                                and (pre[pre[rtarget]] not in self.stmts or self.get_target(pre[pre[rtarget]]) > pre[pre[rtarget]])\
                                and 1 == len(self.remove_mid_line_ifs(self.rem_or(start, pre[pre[rtarget]], PJIF, target))):
                            #0 POP_JUMP_IF_FALSE (op)  ---+
                            #    ...                      |
                            #    POP_JUMP_IF_FALSE (1) ---+
                            #X   ...                      |
                            #    JUMP_ABSOLUTE         ---+
                            #    JUMP_FORWARD/A  --->     |
                            #Y   rtarget                  |  
                            #    ... target            <--+
                            if self.showast: print('@@@6')
                            pass
                        elif code[pre[pre[rtarget]]] == JA and code[pre[pre[pre[rtarget]]]] == JA \
                                and self.remove_mid_line_ifs([pos]) \
                                and target == self.get_target(pre[pre[rtarget]]) == self.get_target(pre[pre[pre[rtarget]]]) \
                                and pre[pre[rtarget]] in self.stmts and self.get_target(pre[pre[rtarget]]) < pre[pre[rtarget]] \
                                and len(self.remove_mid_line_ifs(self.rem_or(start, pre[pre[rtarget]], PJIF, target))) > 0:
                            #0 POP_JUMP_IF_FALSE (op) ---^
                            #    ...
                            #    POP_JUMP_IF_FALSE    ---^
                            #    ...
                            #X   JUMP_ABSOLUTE        ---^
                            #    JUMP_ABSOLUTE        ---^
                            #    JUMP_FORWARD/A       ---^
                            #Y   rtarget
                            if self.showast: print('@@@7')
                            pass
                        elif code[pre[pre[rtarget]]] == RETURN_VALUE \
                                and self.remove_mid_line_ifs([pos]) \
                                and 1 == (len(set(self.remove_mid_line_ifs(self.rem_or(start,
                                                                                       pre[pre[rtarget]],
                                                                                       (PJIF, PJIT), target)))
                                              | set(self.remove_mid_line_ifs(self.rem_or(start, pre[pre[rtarget]],
                                                            (PJIF, PJIT, JA), pre[rtarget], True))))):
                            #0 POP_JUMP_IF_FALSE (op)  ---+
                            #    ...                      |
                            #    POP_JUMP_IF_FALSE     ---+  or  POP_JUMP_IF_FALSE/TRUE/A ---+
                            #X   ...                      |                                  |
                            #    RETURN_VALUE             |                                  |
                            #    JUMP_FORWARD/A  --->     |                               <--+
                            #Y   rtarget                  |
                            #    ... target            <--+
                            if self.showast: print('@@@8')
                            pass
                        else:
                            fix = None
                            jump_ifs = self.all_instr(start, self.next_stmt[pos], PJIF)
                            last_jump_good = True
                            for j in jump_ifs: #find first PJIF with same target as current jump
                                if target == self.get_target(j):
                                    if self.lines[j].next == j+3 and last_jump_good:
                                        fix = j
                                        break
                                else:
                                    last_jump_good = False
                            #0 POP_JUMP_IF_FALSE ---> target
                            #     ...
                            #     POP_JUMP_IF_FALSE (fix or match) ---> target  Add COME_FROM for jump
                            #     ...
                            if self.showast: print('@@@9')
                            self.fixed_jumps[pos] = fix or match[-1] #choose a minimum of them
                            return
                    else:
                        if self.showast: print('@@@10')
                        self.fixed_jumps[pos] = match[-1] #Add COME_FROM for jump
                        return
            else: # op == PJIT
                if (pos+3) in self.load_asserts: #is AssertionError/LOAD_ASSERT
                    if code[pre[rtarget]] == RAISE_VARARGS:
                        return
                    self.load_asserts.remove(pos+3)

                next = self.next_stmt[pos]
                if pre[next] == pos:
                    #  POP_JUMP_IF_TRUE (op)
                    #1 ...next
                    if self.showast: print('@@@11')
                    pass
                elif target < pos and code[rtarget] == code[pre[rtarget]] == JA and pre[rtarget] in self.stmts \
                     and target == self.get_target(rtarget) == self.get_target(pre[rtarget]):
                    #  target...                 <--+
                    #  POP_JUMP_IF_TRUE (pos)    ---+
                    #  ...                          |
                    #1 JUMP_ABSOLUTE (stmt)      ---+
                    #  JUMP_ABSOLUTE (rtarget)   ---+
                    if self.showast: print('@@@12')
                    pass
                elif target > pos and code[target] == code[rtarget] == JA and rtarget < target \
                     and self.get_target(target) == self.get_target(rtarget):
                    #  POP_JUMP_IF_TRUE (pos)       ^   ---+
                    #  ...                          |      |
                    #1 JUMP_ABSOLUTE (rtarget)   ---+      |
                    #  JUMP_ABSOLUTE (target)    ---+   <--+
                    if self.showast: print('@@@13')
                    pass
                elif code[next] in (JF, JA) and target == self.get_target(next):
                    #  POP_JUMP_IF_TRUE (op) ---> target
                    #  ...
                    #1 JUMP_FORWARD/A (next) ---> target
                    if self.showast: print('@@@14')
                    if code[pre[next]] == PJIF:
                        #  POP_JUMP_IF_TRUE (op) ---> target
                        #  ...
                        #  POP_JUMP_IF_FALSE
                        #1 JUMP_FORWARD/A (next) ---> target
                        if self.showast: print('@@@15')
                        if code[next] == JF or target != rtarget or code[pre[pre[rtarget]]] not in (JA, RETURN_VALUE):
                            #  POP_JUMP_IF_TRUE (op) ---> target
                            #  ...
                            #  ... or JUMP_ABSOLUTE or RETURN_VALUE
                            #  POP_JUMP_IF_FALSE                     <--- Add COME_FROM for jump
                            #1 JUMP_FORWARD/A (next) ---> target
                            #X ... rtarget
                            match = self.rem_or(start, next, PJIF, self.get_target(pre[next])) #search all PJIF's between pos and next
                            if match and match[-1] < pre[next]:
                                if self.showast: print('@@@16')
                                self.fixed_jumps[pos] = match[-1] #Add COME_FROM for jump
                            else:
                                if self.showast: print('@@@17')
                                self.fixed_jumps[pos] = pre[next] #Add COME_FROM for jump
                            return
                elif code[next] == JA and code[target] in (JA, JF):
                    #  POP_JUMP_IF_TRUE (op) ---> JUMP_ABSOLUTE or JUMP_FORWARD
                    #  ...
                    #1 JUMP_ABSOLUTE (next) ---> next_target
                    next_target = self.get_target(next)
                    if self.get_target(target) == next_target:
                        #  POP_JUMP_IF_TRUE (op) ---> JUMP_ABSOLUTE or JUMP_FORWARD ---> next_target
                        #  ...                              <--- Add COME_FROM for jump
                        #1 JUMP_ABSOLUTE (next) ---> next_target
                        if self.showast: print('@@@18')
                        match = self.rem_or(start, next, PJIF, target) #search all PJIF's between pos and next
                        if match and match[-1] < pre[next]:
                            if self.showast: print('@@@19')
                            self.fixed_jumps[pos] = match[-1] #Add COME_FROM for jump
                        else:
                            if self.showast: print('@@@20')
                            self.fixed_jumps[pos] = pre[next] #Add COME_FROM for jump
                        return
                    elif code[next_target] in (JA, JF) and self.get_target(next_target) == self.get_target(target):
                        #  POP_JUMP_IF_TRUE (op) ---> JUMP_ABSOLUTE or JUMP_FORWARD ---> x
                        #  ...                          <--- Add COME_FROM for jump
                        #1 JUMP_ABSOLUTE (next) ---> JUMP_ABSOLUTE or JUMP_FORWARD ---> x
                        if self.showast: print('@@@21')
                        match = self.rem_or(start, next, PJIF, target) #search all PJIF's between pos and next
                        if match and match[-1] < pre[next]:
                            if self.showast: print('@@@22')
                            self.fixed_jumps[pos] = match[-1] #Add COME_FROM for jump
                        else:
                            if self.showast: print('@@@23')
                            self.fixed_jumps[pos] = pre[next] #Add COME_FROM for jump
                        return

            # don't add a struct for a while test, it's already taken care of
            if pos in self.ignore_if: #if (PJIF, PJIT) in SETUP_LOOP
                if pos in self.ignore_if_SL and code[target] == POP_BLOCK:
                    #0 SETUP_LOOP                ---+
                    #    ...POP_JUMP_IF_X        ---+  Add COME_FROM for jump
                    #    ...                        |
                    #    POP_BLOCK (test_target) <--+
                    if self.showast: print('@@@24')
                    for x in self.fixed_jumps.values():
                        if target == x:
                            return
                    self.fixed_jumps[pos] = target #Add COME_FROM for jump
                return

            #JA,JA,JD with additional line_no
            if code[pre[rtarget]] == JA and pre[rtarget] in self.stmts and pre[rtarget] != pos and pre[pre[rtarget]] != pos:
                #  POP_JUMP_IF_FALSE/TRUE  --->
                #1   start
                #    ...
                #X   JUMP_ABSOLUTE    --+
                #    rtarget            |
                #    ...             <--+
                if self.showast: print('@@@25')
                if code[rtarget] == JA and code[rtarget+3] == POP_BLOCK:
                    #    ...
                    #X   JUMP_ABSOLUTE          --+
                    #    JUMP_ABSOLUTE (rtarget)  |
                    #    POP_BLOCK                v
                    if code[pre[pre[rtarget]]] != JA:
                        if self.showast: print('@@@26')
                        pass
                    elif self.get_target(pre[pre[rtarget]]) != target:
                        if self.showast: print('@@@27')
                        pass
                    else:
                        #    JUMP_ABSOLUTE              ---+
                        #X   JUMP_ABSOLUTE          --+    |  <-- set as rtarget
                        #    JUMP_ABSOLUTE (rtarget)  | <--+
                        #    POP_BLOCK                v
                        if self.showast: print('@@@28')
                        rtarget = pre[rtarget]
                else:
                    #X   JUMP_ABSOLUTE    --+    |   <-- set as rtarget
                    #    rtarget            | <--+
                    #    ...             <--+
                    if self.showast: print('@@@29')
                    rtarget = pre[rtarget] 

            # does the if jump just beyond a jump op, then this is probably an if statement
            if code[pre[rtarget]] in (JA, JF):
                if_end = self.get_target(pre[rtarget])

                # is this a loop not an if?
                if (if_end < pre[rtarget]) and (code[pre[if_end]] in [SETUP_LOOP, GET_ITER]):
                    if if_end < start:
                        if target > start and not code[rtarget] in (JA, JF, POP_BLOCK):
                            if self.showast: print('@@@30')
                            self.structs.append({'type':  'if-then',
                                                   'start': start,
                                                   'end':   pre[rtarget]})
                            self.not_continue.add(pre[rtarget])
                            self.JA_to_shortJF.add(pre[rtarget])
                            self.shortJF_links[pre[rtarget]] = rtarget
                            return
                    elif if_end >= start: # is this a loop not an if?
                        if self.showast: print('@@@31')
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
                #  POP_JUMP_IF_FALSE/TRUE --+
                #1   start                  |
                #    ...                    |
                #    RETURN_VALUE           |
                #X   target (~rtarget)   <--+
                need_JF = False
                if parent['type'] == 'root':
                    if_end = self.first_instr(rtarget, len(code), RETURN_VALUE)
                    if if_end == parent['end']:
                        #check forward
                        need_JF = True
                        for x in self.stmts_full:
                            if start <= x < pre[rtarget] or rtarget <= x < if_end:
                                need_JF = False
                                break
                if need_JF:
                    self.structs.append({'type':  'if-then',
                                           'start': start,
                                           'end':   pre[rtarget]})
                    self.not_continue.add(pre[rtarget])
                    if rtarget < if_end:
                        self.structs.append({'type':  'if-else',
                                           'start': rtarget,
                                           'end':   if_end})
                    self.return_end_ifs_rep_to_JF.add(pre[rtarget])
                    self.JF_links[pre[rtarget]] = if_end
                else:
                    self.structs.append({'type':  'if-then',
                                           'start': start,
                                           'end':   pre[rtarget]})
                    self.return_end_ifs.add(pre[rtarget])

        elif op in (JUMP_IF_FALSE_OR_POP, JUMP_IF_TRUE_OR_POP):
            target = self.get_target(pos, op)
            self.fixed_jumps[pos] = self.restrict_to_parent(target, parent)
        elif op in (JF, JA):
            target = self.get_target(pos, op)
            if code[target] == RETURN_VALUE and code[pre[pos]] == COMPARE_OP:
                #0 COMPARE_OP
                #1 JUMP_ABSOLUTE/FORWARD --> RETURN_VEALUE (target)
                self.JA_to_RV.add(pos)

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
        self.ignore_if_SL = set() #for SETUP_LOOP
        self.build_stmt_indices()
        # Containers filled by detect_structure()
        self.not_continue = set()
        self.continue_oneline = set() #loop as ...<condition>:<operator>...
        self.return_end_ifs = set()
        self.return_end_ifs_rep_to_JF = set() #replace ifs to JUMP_FORWARD
        self.JF_links = dict() #targets for JUMP_FORWARD
        self.JA_to_RV = set() #replace JUMP_ABSOLUTE to RETURN_VALUE
        self.JA_to_shortJF = set()   #replace JUMP_ABSOLUTE to short JUMP_FORWARD
        self.shortJF_links = dict()  #targets for short JUMP_FORWARD
        self.add_additional_PB = set() #add a second POP_BLOCK

        if self.showast:
            print('\n--- Detect structure and jumps targets: ---\n')

        targets = {}
        for i in self.op_range(0, n):
            op = self.code[i]

            # Determine structures and fix jumps in Python versions
            # since 2.3
            len_structs = len(self.structs)
            self.detect_structure(i, op)
            if self.showast:
                print('%d %s' % (i, opname[op]))
                if len(self.structs) != len_structs:
                    for x in self.structs:
                        print(x)
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
        for x,y in self.JF_links.items():
            if not y in targets:
                targets[y] = [x]
            elif not x in targets[y]:
                targets[y].append(x)
        for x,y in self.shortJF_links.items():
            if not y in targets:
                targets[y] = [x]
            elif not x in targets[y]:
                targets[y].append(x)
        return targets

if __name__ == "__main__":
    co = inspect.currentframe().f_code
    tokens, customize = Scanner27().disassemble(co)
    for t in tokens:
        print(t)

