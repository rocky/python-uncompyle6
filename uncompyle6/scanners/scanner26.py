#  Copyright (c) 2015, 2016 by Rocky Bernstein
#  Copyright (c) 2005 by Dan Pascu <dan@windowmaker.org>
#  Copyright (c) 2000-2002 by hartmut Goebel <h.goebel@crazy-compilers.com>
#  Copyright (c) 1999 John Aycock

"""
Python 2.6 bytecode scanner

This overlaps Python's 2.6's dis module, but it can be run from Python 3 and
other versions of Python. Also, we save token information for later
use in deparsing.
"""

from collections import namedtuple
from array import array

from uncompyle6.opcodes.opcode_26 import *
import dis
import uncompyle6.scanner as scan

class Scanner26(scan.Scanner):
    def __init__(self):
        scan.Scanner.__init__(self, 2.6)

    def disassemble(self, co, classname=None, code_objects={}):
        '''
        Disassemble a code object, returning a list of 'Token'.

        The main part of this procedure is modelled after
        dis.disassemble().
        '''

        # import dis; dis.disassemble(co) # DEBUG

        # Container for tokens
        tokens = []

        customize = {}
        Token = self.Token # shortcut
        self.code = array('B', co.co_code)
        for i in self.op_range(0, len(self.code)):
            if self.code[i] in (RETURN_VALUE, END_FINALLY):
                n = i + 1
        self.code = array('B', co.co_code[:n])
        # linestarts contains block code adresses (addr,block)
        self.linestarts = list(dis.findlinestarts(co))
        self.prev = [0]
        # class and names
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
        self.names = names

        # list of instruction to remove/add or change to match with bytecode 2.7
        self.toChange = []
        self.restructBytecode()
        codelen = len(self.code)
        # mapping adresses of prev instru
        for i in self.op_range(0, codelen):
            op = self.code[i]
            self.prev.append(i)
            if self.op_hasArgument(op):
                self.prev.append(i)
                self.prev.append(i)
        j = 0
        linestarts = self.linestarts
        self.lines = []
        linetuple = namedtuple('linetuple', ['l_no', 'next'])

        # linestarts is a tuple of (offset, line number).
        # Turn that in a has that we can index
        linestartoffsets = {}
        for offset, lineno in linestarts:
            linestartoffsets[offset] = lineno

        (prev_start_byte, prev_line_no) = linestarts[0]
        for (start_byte, line_no) in linestarts[1:]:
            while j < start_byte:
                self.lines.append(linetuple(prev_line_no, start_byte))
                j += 1
            prev_line_no = line_no
        while j < codelen:
            self.lines.append(linetuple(prev_line_no, codelen))
            j+=1
        # self.lines contains (block,addrLastInstr)

        self.load_asserts = set()
        for i in self.op_range(0, codelen):
            if self.code[i] == PJIT and self.code[i+3] == LOAD_GLOBAL:
                if names[self.get_argument(i+3)] == 'AssertionError':
                    self.load_asserts.add(i+3)

        cf = self.find_jump_targets(self.code)
        # contains (code, [addrRefToCode])

        last_stmt = self.next_stmt[0]
        i = self.next_stmt[last_stmt]
        replace = {}
        while i < codelen-1:
            if self.lines[last_stmt].next > i:
                if self.code[last_stmt] == PRINT_ITEM:
                    if self.code[i] == PRINT_ITEM:
                        replace[i] = 'PRINT_ITEM_CONT'
                    elif self.code[i] == PRINT_NEWLINE:
                        replace[i] = 'PRINT_NEWLINE_CONT'
            last_stmt = i
            i = self.next_stmt[i]

        imports = self.all_instr(0, codelen, (IMPORT_NAME, IMPORT_FROM, IMPORT_STAR))
        if len(imports) > 1:
            last_import = imports[0]
            for i in imports[1:]:
                if self.lines[last_import].next > i:
                    if self.code[last_import] == IMPORT_NAME == self.code[i]:
                        replace[i] = 'IMPORT_NAME_CONT'
                last_import = i

        extended_arg = 0
        for offset in self.op_range(0, codelen):
            op = self.code[offset]
            op_name = self.opname[op]
            oparg = None; pattr = None

            if offset in cf:
                k = 0
                for j in cf[offset]:
                    tokens.append(Token('COME_FROM', None, repr(j),
                                    offset="%s_%d" % (offset, k) ))
                    k += 1
            if self.op_hasArgument(op):
                oparg = self.get_argument(offset) + extended_arg
                extended_arg = 0
                if op == EXTENDED_ARG:
                    raise NotImplementedError
                    extended_arg = oparg * scan.L65536
                    continue
                if op in hasconst:
                    const = co.co_consts[oparg]
                    # We can't use inspect.iscode() because we may be
                    # using a different version of Python than the
                    # one that this was byte-compiled on. So the code
                    # types may mismatch.
                    if hasattr(const, 'co_name'):
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
                        # verify uses 'pattr' for comparison, since 'attr'
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
                    try:
                        pattr = cmp_op[oparg]
                    except:
                        from trepan.api import debug; debug()
                elif op in hasfree:
                    pattr = free[oparg]
            if offset in self.toChange:
                if self.code[offset] == JA and self.code[oparg] == WITH_CLEANUP:
                    op_name = 'SETUP_WITH'
                    cf[oparg] = cf.get(oparg, []) + [offset]
            if op in (BUILD_LIST, BUILD_TUPLE, BUILD_SLICE,
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

            if offset in linestartoffsets:
                linestart = linestartoffsets[offset]
            else:
                linestart = None

            if offset not in replace:
                tokens.append(Token(op_name, oparg, pattr, offset, linestart))
            else:
                tokens.append(Token(replace[offset], oparg, pattr, offset, linestart))
                pass
            pass

        # Debug
        # for t in tokens:
        #     print t
        return tokens, customize

    def getOpcodeToDel(self, i):
        '''
        check validity of the opcode at position I and return a list of opcode to delete
        '''
        opcode = self.code[i]
        opsize = self.op_size(opcode)

        if i+opsize >= len(self.code):
            return None

        if opcode == EXTENDED_ARG:
            raise NotImplementedError
        # modification of some jump structure
        if opcode in (PJIF, PJIT, JA, JF, RETURN_VALUE):
            toDel = []
            # del POP_TOP
            if self.code[i+opsize] == POP_TOP:
                if self.code[i+opsize] == self.code[i+opsize+1] and self.code[i+opsize] == self.code[i+opsize+2] \
                and opcode in (JF, JA) and self.code[i+opsize] != self.code[i+opsize+3]:
                    pass
                else:
                    toDel += [i+opsize]
            # conditional tuple (not optimal at all, no good solution...)
            if self.code[i] == JA and self.code[i+opsize] == POP_TOP \
                and self.code[i+opsize+1] == JA and self.code[i+opsize+4] == POP_BLOCK:
                jmpabs1target = self.get_target(i)
                jmpabs2target = self.get_target(i+opsize+1)
                if jmpabs1target == jmpabs2target and self.code[jmpabs1target] == FOR_ITER \
                and self.code[jmpabs1target-1] != GET_ITER:
                    destFor = self.get_target(jmpabs1target)
                    if destFor == i+opsize+4:
                        setupLoop = self.last_instr(0, jmpabs1target, SETUP_LOOP)
                        standarFor =  self.last_instr(setupLoop, jmpabs1target, GET_ITER)
                        if standarFor is None:
                            self.restructJump(jmpabs1target, destFor+self.op_size(POP_BLOCK))
                            toDel += [setupLoop, i+opsize+1, i+opsize+4]

            if len(toDel) > 0:
                return toDel
            return None
        # raise_varags not realy handle for the moment
        if opcode == RAISE_VARARGS:
            if self.code[i+opsize] == POP_TOP:
                return [i+opsize]
        # modification of list structure
        if opcode == BUILD_LIST:
            if (self.code[i+opsize] == DUP_TOP and
                self.code[i+opsize+1] in (STORE_NAME, STORE_FAST)):
                # del DUP/STORE_NAME x
                toDel = [i+opsize, i+opsize+1]
                nameDel = self.get_argument(i+opsize+1)
                start = i+opsize+1
                end = start
                # del LOAD_NAME x
                while end < len(self.code):
                    end = self.first_instr(end, len(self.code), (LOAD_NAME, LOAD_FAST))
                    if nameDel == self.get_argument(end):
                        toDel += [end]
                        break
                    if self.code[end] == LOAD_NAME:
                        end += self.op_size(LOAD_NAME)
                    else:
                        end += self.op_size(LOAD_FAST)
                # log JA/POP_TOP to del and update PJIF
                while start < end:
                    start = self.first_instr(start, end, (PJIF, PJIT))
                    if start is None: break
                    target = self.get_target(start)
                    if self.code[target] == POP_TOP and self.code[target-3] == JA:
                        toDel += [target, target-3]
                        # update PJIF
                        target = self.get_target(target-3)
                        self.restructJump(start, target)
                    start += self.op_size(PJIF)
                # del DELETE_NAME x
                start = end
                while end < len(self.code):
                    end = self.first_instr(end, len(self.code),
                                           (DELETE_NAME, DELETE_FAST))
                    if nameDel == self.get_argument(end):
                        toDel += [end]
                        break
                    if self.code[end] == DELETE_NAME:
                        end += self.op_size(DELETE_NAME)
                    else:
                        end += self.op_size(DELETE_FAST)
                return toDel
        # for / while struct
        if opcode == SETUP_LOOP:
            # change join(for..) struct
            if self.code[i+3] == LOAD_FAST and self.code[i+6] == FOR_ITER:
                end = self.first_instr(i, len(self.code), RETURN_VALUE)
                end = self.first_instr(i, end, YIELD_VALUE)
                if end and self.code[end+1] == POP_TOP and self.code[end+2] == JA and self.code[end+5] == POP_BLOCK:
                    return [i, end+5]
        # with stmt
        if opcode == WITH_CLEANUP:
            allRot = self.all_instr(0, i, (ROT_TWO))
            chckRot = -1
            for rot in allRot:
                if self.code[rot+1] == LOAD_ATTR and self.code[rot-3] == LOAD_ATTR \
                    and self.code[rot-4] == DUP_TOP:
                    chckRot = rot
            assert chckRot > 0
            toDel = [chckRot-4, chckRot-3, chckRot]
            chckStp = -1
            allSetup = self.all_instr(chckRot+1, i, (SETUP_FINALLY))
            for stp in allSetup:
                if i == self.get_target(stp):
                    chckStp = stp
            assert chckStp > 0
            toDel += [chckStp]
            chckDel = chckRot+1+self.op_size(self.code[chckRot+1])
            while chckDel < chckStp-3:
                toDel += [chckDel]
                chckDel += self.op_size(self.code[chckDel])
            if (self.code[chckStp-3] in (STORE_NAME, STORE_FAST) and
                self.code[chckStp+3] in (LOAD_NAME, LOAD_FAST)
                and self.code[chckStp+6] in (DELETE_NAME, DELETE_FAST)):
                toDel += [chckStp-3, chckStp+3, chckStp+6]
            # SETUP_WITH opcode dosen't exist in 2.6 but is necessary for the grammar
            self.code[chckRot+1] = JUMP_ABSOLUTE # ugly hack
            self.restructJump(chckRot+1, i)
            self.toChange.append(chckRot+1)
            return toDel
        if opcode == NOP:
            return [i]
        return None

    def getOpcodeToExp(self):
        # we handle listExp, if opcode have to be resized
        listExp = []
        i=0
        while i < len(self.code): # we can't use op_range for the moment
            op = self.code[i]
            if op in self.opc.hasArgumentExtended:
                listExp += [i]
            elif self.op_hasArgument(op):
                i+=2
            i+=1
        return listExp

    def restructCode(self, listDel, listExp):
        '''
        restruct linestarts and jump destination after converting bytecode
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
                if op in hasjrel+hasjabs:
                    offset = 0
                    jmpTarget = self.get_target(jmp)
                    for toDel in listDel:
                        if toDel < jmpTarget:
                            if op in hasjabs or jmp < toDel:
                                offset-=self.op_size(self.code[toDel])
                    self.restructJump(jmp, jmpTarget+offset)
        if listExp:
            jmp = 0
            while jmp < len(self.code): # we can't use op_range for the moment
                op = self.code[jmp]
                if op in hasjrel+hasjabs:
                    offset = 0
                    jmpTarget = self.get_target(jmp)
                    for toExp in listExp:
                        if toExp < jmpTarget:
                            if op in hasjabs or jmp < toExp:
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

    def restructRelativeJump(self):
        '''
        change relative JUMP_IF_FALSE/TRUE to absolut jump
        and remap the target of PJIF/PJIT
        '''
        i=0
        while i < len(self.code): # we can't use op_range for the moment
            op = self.code[i]
            if(op in (PJIF, PJIT)):
                target = self.get_argument(i)
                target += i + 3
                self.restructJump(i, target)
            if self.op_hasArgument(op) and op not in self.opc.hasArgumentExtended:
                i += 3
            else: i += 1

        i=0
        while i < len(self.code): # we can't use op_range for the moment
            op = self.code[i]
            if(op in (PJIF, PJIT)):
                target = self.get_target(i)
                if self.code[target] == JA:
                    target = self.get_target(target)
                    self.restructJump(i, target)
            if self.op_hasArgument(op) and op not in self.opc.hasArgumentExtended:
                i += 3
            else: i += 1

    def restructJump(self, pos, newTarget):
        if not (self.code[pos] in hasjabs+hasjrel):
            raise 'Can t change this argument. Opcode is not a jump'
        if newTarget > 0xFFFF:
            raise NotImplementedError
        offset = newTarget-self.get_target(pos)
        target = self.get_argument(pos)+offset
        if target < 0 or target > 0xFFFF:
            raise NotImplementedError
        self.code[pos+2] = (target >> 8) & 0xFF
        self.code[pos+1] = target & 0xFF

    def build_stmt_indices(self):
        code = self.code
        start = 0
        end = len(code)

        stmt_opcodes = set([
            SETUP_LOOP, BREAK_LOOP, CONTINUE_LOOP,
            SETUP_FINALLY, END_FINALLY, SETUP_EXCEPT,
            POP_BLOCK, STORE_FAST, DELETE_FAST, STORE_DEREF,
            STORE_GLOBAL, DELETE_GLOBAL, STORE_NAME, DELETE_NAME,
            STORE_ATTR, DELETE_ATTR, STORE_SUBSCR, DELETE_SUBSCR,
            RETURN_VALUE, RAISE_VARARGS, POP_TOP,
            PRINT_EXPR, PRINT_ITEM, PRINT_NEWLINE, PRINT_ITEM_TO, PRINT_NEWLINE_TO,
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
            except_match = self.first_instr(start, len(self.code), (PJIF))
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
                    if self.code[self.prev[i]] == NOP:
                        i = self.prev[i]
                    assert self.code[self.prev[i]] in (JA, JF, RETURN_VALUE)
                    self.not_continue.add(self.prev[i])
                    return self.prev[i]
                count_END_FINALLY += 1
            elif op in (SETUP_EXCEPT, SETUP_FINALLY):
                count_SETUP_ += 1
        # return self.lines[start].next

    def detect_structure(self, pos, op=None):
        '''
        Detect type of block structures and their boundaries to fix optimizied jumps
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
                jump_back = self.last_instr(start, end, RETURN_VALUE)
                if not jump_back:
                    return
                jump_back += 1
                if code[self.prev[next_line_byte]] not in (PJIF, PJIT):
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
            while i < len(self.code) and self.code[i] != END_FINALLY:
                jmp = self.next_except_jump(i)
                if jmp is None: # check
                    i = self.next_stmt[i]
                    continue
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
                                       'start': i+2, # check
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
                    elif pos < rtarget and code[target] == ROT_TWO:
                        self.fixed_jumps[pos] = target
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
                # if it's an old JUMP_IF_FALSE_OR_POP, JUMP_IF_TRUE_OR_POP (return 1<2<3 case)
                if pos < rtarget and code[rtarget] == ROT_TWO:
                    return
                self.structs.append({'type':  'if-then',
                                       'start': start,
                                       'end':   rtarget})
                self.return_end_ifs.add(pre[rtarget])

    def find_jump_targets(self, code):
        '''
        Detect all offsets in a byte code which are jump targets.

        Return the list of offsets.

        This procedure is modelled after dis.findlabels(), but here
        for each target the number of jumps are counted.
        '''

        n = len(code)
        self.structs = [{'type':  'root',
                           'start': 0,
                           'end':   n-1}]
        self.loops = []  # All loop entry points
        self.fixed_jumps = {} # Map fixed jumps to their real destination
        self.ignore_if = set()
        self.build_stmt_indices()
        self.not_continue = set()
        self.return_end_ifs = set()

        targets = {}
        for i in self.op_range(0, n):
            op = code[i]

            # Determine structures and fix jumps for 2.3+
            self.detect_structure(i, op)

            if self.op_hasArgument(op):
                label = self.fixed_jumps.get(i)
                oparg = self.get_argument(i)
                if label is None:
                    if op in hasjrel and op != FOR_ITER:
                        label = i + 3 + oparg
                    # elif op in hasjabs:
                    #     if op in (JUMP_IF_FALSE, JUMP_IF_TRUE):
                    #         if (oparg > i):
                    #             label = oparg
                if label is not None and label != -1:
                    targets[label] = targets.get(label, []) + [i]
            elif op == END_FINALLY and i in self.fixed_jumps:
                label = self.fixed_jumps[i]
                targets[label] = targets.get(label, []) + [i]
        return targets

if __name__ == "__main__":
    from uncompyle6 import PYTHON_VERSION
    if PYTHON_VERSION == 2.6:
        import inspect
        co = inspect.currentframe().f_code
        tokens, customize = Scanner26().disassemble(co)
        for t in tokens:
            print(t.format())
    else:
        print("Need to be Python 2.6 to demo; I am %s." %
              PYTHON_VERSION)
