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

from xdis.bytecode import findlinestarts
import uncompyle6.scanners.scanner2 as scan

# bytecode verification, verify(), uses JUMP_OPs from here
from xdis.opcodes import opcode_26
JUMP_OPs = opcode_26.JUMP_OPs

class Scanner26(scan.Scanner2):
    def __init__(self, show_asm=False):
        super(Scanner26, self).__init__(2.6, show_asm)
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

    def disassemble(self, co, classname=None, code_objects={}, show_asm=None):
        '''
        Disassemble a code object, returning a list of 'Token'.

        The main part of this procedure is modelled after
        dis.disassemble().
        '''

        show_asm = self.show_asm if not show_asm else show_asm
        if self.show_asm in ('both', 'before'):
            from xdis.bytecode import Bytecode
            bytecode = Bytecode(co, self.opc)
            for instr in bytecode.get_instructions(co):
                print(instr._disassemble())

        # from xdis.bytecode import Bytecode
        # bytecode = Bytecode(co, self.opc)
        # for instr in bytecode.get_instructions(co):
        #     print(instr._disassemble())

        # Container for tokens
        tokens = []

        customize = {}
        Token = self.Token # shortcut

        n = self.setup_code(co)

        self.build_lines_data(co, n-1)

        # linestarts contains block code adresses (addr,block)
        self.linestarts = list(findlinestarts(co))

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

        self.build_prev_op(codelen)

        self.load_asserts = set()
        for i in self.op_range(0, codelen):
            if self.code[i] == self.opc.PJIT and self.code[i + 3] == self.opc.LOAD_GLOBAL:
                if names[self.get_argument(i+3)] == 'AssertionError':
                    self.load_asserts.add(i+3)

        cf = self.find_jump_targets()
        # contains (code, [addrRefToCode])

        last_stmt = self.next_stmt[0]
        i = self.next_stmt[last_stmt]
        replace = {}
        while i < codelen - 1:
            if self.lines[last_stmt].next > i:
                if self.code[last_stmt] == self.opc.PRINT_ITEM:
                    if self.code[i] == self.opc.PRINT_ITEM:
                        replace[i] = 'PRINT_ITEM_CONT'
                    elif self.code[i] == self.opc.PRINT_NEWLINE:
                        replace[i] = 'PRINT_NEWLINE_CONT'
            last_stmt = i
            i = self.next_stmt[i]

        imports = self.all_instr(0, codelen,
                                (self.opc.IMPORT_NAME, self.opc.IMPORT_FROM,
                                 self.opc.IMPORT_STAR))
        if len(imports) > 1:
            last_import = imports[0]
            for i in imports[1:]:
                if self.lines[last_import].next > i:
                    if self.code[last_import] == self.opc.IMPORT_NAME == self.code[i]:
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
                if op == self.opc.EXTENDED_ARG:
                    raise NotImplementedError
                    extended_arg = oparg * scan.L65536
                    continue
                if op in self.opc.hasconst:
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
                        # pattr = 'code_object @ 0x%x %s->%s' % \
                        # (id(const), const.co_filename, const.co_name)
                        pattr = '<code_object ' + const.co_name + '>'
                    else:
                        pattr = const
                elif op in self.opc.hasname:
                    pattr = names[oparg]
                elif op in self.opc.hasjrel:
                    pattr = repr(offset + 3 + oparg)
                elif op in self.opc.hasjabs:
                    pattr = repr(oparg)
                elif op in self.opc.haslocal:
                    pattr = varnames[oparg]
                elif op in self.opc.hascompare:
                    pattr = self.opc.cmp_op[oparg]
                elif op in self.opc.hasfree:
                    pattr = free[oparg]
            if offset in self.toChange:
                if (self.code[offset] == self.opc.JA and
                    self.code[oparg] == self.opc.WITH_CLEANUP):
                    op_name = 'SETUP_WITH'
                    cf[oparg] = cf.get(oparg, []) + [offset]
            if op in self.varargs_ops:
                # CE - Hack for >= 2.5
                #      Now all values loaded via LOAD_CLOSURE are packed into
                #      a tuple before calling MAKE_CLOSURE.
                if (op == self.opc.BUILD_TUPLE and
                    self.code[self.prev[offset]] == self.opc.LOAD_CLOSURE):
                    continue
                else:
                    op_name = '%s_%d' % (op_name, oparg)
                    if op != self.opc.BUILD_SLICE:
                        customize[op_name] = oparg
            elif op == self.opc.JA:
                target = self.get_target(offset)
                if target < offset:
                    if (offset in self.stmts
                        and self.code[offset + 3] not in (self.opc.END_FINALLY,
                                                          self.opc.POP_BLOCK)
                        and offset not in self.not_continue):
                        op_name = 'CONTINUE'
                    else:
                        op_name = 'JUMP_BACK'

            elif op == self.opc.LOAD_GLOBAL:
                if offset in self.load_asserts:
                    op_name = 'LOAD_ASSERT'
            elif op == self.opc.RETURN_VALUE:
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
                pass
            pass

        if self.show_asm:
            for t in tokens:
                print(t)
            print()
        return tokens, customize

    def getOpcodeToDel(self, i):
        '''
        check validity of the opcode at position I and return a list of opcode to delete
        '''
        opcode = self.code[i]
        opsize = self.op_size(opcode)

        if i+opsize >= len(self.code):
            return None

        if opcode == self.opc.EXTENDED_ARG:
            raise NotImplementedError

        # modification of some jump structures
        if opcode in (self.opc.PJIF,
                     self.opc.PJIT,
                     self.opc.JA,
                     self.opc.JF,
                     self.opc.RETURN_VALUE):
            toDel = []
            # del POP_TOP
            if self.code[i+opsize] == self.opc.POP_TOP:
                if self.code[i+opsize] == self.code[i+opsize+1] and self.code[i+opsize] == self.code[i+opsize+2] \
                and opcode in self.jump_forward and self.code[i+opsize] != self.code[i+opsize+3]:
                    pass
                else:
                    toDel += [i+opsize]
            # conditional tuple (not optimal at all, no good solution...)
            if self.code[i] == self.opc.JA and self.code[i+opsize] == self.opc.POP_TOP \
                and self.code[i+opsize+1] == self.opc.JA and self.code[i+opsize+4] == self.opc.POP_BLOCK:
                jmpabs1target = self.get_target(i)
                jmpabs2target = self.get_target(i+opsize+1)
                if jmpabs1target == jmpabs2target and self.code[jmpabs1target] == self.opc.FOR_ITER \
                and self.code[jmpabs1target-1] != self.opc.GET_ITER:
                    destFor = self.get_target(jmpabs1target)
                    if destFor == i+opsize+4:
                        setupLoop = self.last_instr(0, jmpabs1target, self.opc.SETUP_LOOP)
                        standarFor =  self.last_instr(setupLoop, jmpabs1target, self.opc.GET_ITER)
                        if standarFor is None:
                            self.restructJump(jmpabs1target, destFor+self.op_size(self.opc.POP_BLOCK))
                            toDel += [setupLoop, i+opsize+1, i+opsize+4]

            if len(toDel) > 0:
                return toDel
            return None
        # raise_varagsis  not really handled for the moment
        if opcode == self.opc.RAISE_VARARGS:
            if self.code[i+opsize] == self.opc.POP_TOP:
                return [i+opsize]

        # modification of list structure
        if opcode == self.opc.BUILD_LIST:
            if (self.code[i+opsize] == self.opc.DUP_TOP and
                self.code[i+opsize+1] in (self.opc.STORE_NAME, self.opc.STORE_FAST)):
                # del DUP/STORE_NAME x
                toDel = [i+opsize, i+opsize+1]
                nameDel = self.get_argument(i+opsize+1)
                start = i+opsize+1
                end = start
                # del LOAD_NAME x
                while end < len(self.code):
                    end = self.first_instr(end, len(self.code), (self.opc.LOAD_NAME, self.opc.LOAD_FAST))
                    if nameDel == self.get_argument(end):
                        toDel += [end]
                        break
                    if self.code[end] == self.opc.LOAD_NAME:
                        end += self.op_size(self.opc.LOAD_NAME)
                    else:
                        end += self.op_size(self.opc.LOAD_FAST)
                # log JA/POP_TOP to del and update PJIF
                while start < end:
                    start = self.first_instr(start, end, self.pop_jump_if)
                    if start is None: break
                    target = self.get_target(start)
                    if self.code[target] == self.opc.POP_TOP and self.code[target-3] == self.opc.JA:
                        toDel += [target, target-3]
                        # update PJIF
                        target = self.get_target(target-3)
                        self.restructJump(start, target)
                    start += self.op_size(self.opc.PJIF)
                # del DELETE_NAME x
                start = end
                while end < len(self.code):
                    end = self.first_instr(end, len(self.code),
                                           (self.opc.DELETE_NAME, self.opc.DELETE_FAST))
                    if end:
                        if nameDel == self.get_argument(end):
                            toDel += [end]
                            break
                        if self.code[end] == self.opc.DELETE_NAME:
                            end += self.op_size(self.opc.DELETE_NAME)
                        else:
                            end += self.op_size(self.opc.DELETE_FAST)
                return toDel
        # for / while struct
        if opcode == self.opc.SETUP_LOOP:
            # change join(for..) struct
            if self.code[i+3] == self.opc.LOAD_FAST and self.code[i+6] == self.opc.FOR_ITER:
                end = self.first_instr(i, len(self.code), self.opc.RETURN_VALUE)
                end = self.first_instr(i, end, self.opc.YIELD_VALUE)
                if end and self.code[end+1] == self.opc.POP_TOP and self.code[end+2] == self.opc.JA and self.code[end+5] == self.opc.POP_BLOCK:
                    return [i, end+5]
        # with stmt
        if opcode == self.opc.WITH_CLEANUP:
            allRot = self.all_instr(0, i, (self.opc.ROT_TWO))
            chckRot = -1
            for rot in allRot:
                if self.code[rot+1] == self.opc.LOAD_ATTR and self.code[rot-3] == self.opc.LOAD_ATTR \
                    and self.code[rot-4] == self.opc.DUP_TOP:
                    chckRot = rot
            assert chckRot > 0
            toDel = [chckRot-4, chckRot-3, chckRot]
            chckStp = -1
            allSetup = self.all_instr(chckRot+1, i, (self.opc.SETUP_FINALLY))
            for stp in allSetup:
                if i == self.get_target(stp):
                    chckStp = stp
            assert chckStp > 0
            toDel += [chckStp]
            chckDel = chckRot+1+self.op_size(self.code[chckRot+1])
            while chckDel < chckStp-3:
                toDel += [chckDel]
                chckDel += self.op_size(self.code[chckDel])
            if (self.code[chckStp-3] in (self.opc.STORE_NAME, self.opc.STORE_FAST) and
                self.code[chckStp+3] in (self.opc.LOAD_NAME, self.opc.LOAD_FAST)
                and self.code[chckStp+6] in (self.opc.DELETE_NAME, self.opc.DELETE_FAST)):
                toDel += [chckStp-3, chckStp+3, chckStp+6]
            # SETUP_WITH opcode dosen't exist in 2.6 but is necessary for the grammar
            self.code[chckRot+1] = self.opc.JUMP_ABSOLUTE # ugly hack
            self.restructJump(chckRot+1, i)
            self.toChange.append(chckRot+1)
            return toDel
        if opcode == self.opc.NOP:
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

    def restructRelativeJump(self):
        '''
        change relative JUMP_IF_FALSE/TRUE to absolut jump
        and remap the target of PJIF/PJIT
        '''
        i=0
        while i < len(self.code): # we can't use op_range for the moment
            op = self.code[i]
            if op in self.pop_jump_if:
                target = self.get_argument(i)
                target += i + 3
                self.restructJump(i, target)
            i += self.op_size(op)

        i=0
        while i < len(self.code): # we can't use op_range for the moment
            op = self.code[i]
            if op in self.pop_jump_if:
                target = self.get_target(i)
                if self.code[target] == self.opc.JA:
                    target = self.get_target(target)
                    self.restructJump(i, target)
            i += self.op_size(op)
        i=0
        # while i < len(self.code): # we can't use op_range for the moment
        #     op = self.code[i]
        #     name = self.opc.opname[op]
        #     if self.op_hasArgument(op):
        #         oparg = self.get_argument(i)
        #         print("%d %s %d" % (i, name, oparg))
        #     else:
        #         print("%d %s" % (i, name))
        #     i += self.op_size(op)

    def restructJump(self, pos, newTarget):
        if self.code[pos] not in self.opc.hasjabs + self.opc.hasjrel:
            raise 'Can t change this argument. Opcode is not a jump'
        if newTarget > 0xFFFF:
            raise NotImplementedError
        offset = newTarget-self.get_target(pos)
        target = self.get_argument(pos)+offset
        if target < 0 or target > 0xFFFF:
            raise NotImplementedError
        self.code[pos+2] = (target >> 8) & 0xFF
        self.code[pos+1] = target & 0xFF

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

        if op == self.opc.SETUP_LOOP:
            start = pos+3
            target = self.get_target(pos, op)
            end    = self.restrict_to_parent(target, parent)

            if target != end:
                self.fixed_jumps[pos] = end

            (line_no, next_line_byte) = self.lines[pos]
            jump_back = self.last_instr(start, end, self.opc.JA, next_line_byte, False)
            if (jump_back and jump_back != self.prev[end]
                and code[jump_back + 3] in self.jump_forward):
                if (code[self.prev[end]] == self.opc.RETURN_VALUE
                    or (code[self.prev[end]] == self.opc.POP_BLOCK
                    and code[self.prev[self.prev[end]]] == self.opc.RETURN_VALUE)):
                    jump_back = None
            if not jump_back: # loop suite ends in return. wtf right?
                jump_back = self.last_instr(start, end, self.opc.JA, start, False)
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
                    jump_back = self.last_instr(start, end, self.opc.JA, start, False)
                if end > jump_back + 4 and code[end] in self.jump_forward:
                    if code[jump_back + 4] in (self.opc.JA, self.opc.JF):
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
                # print target, end, parent
            # Add the try block
            self.structs.append({'type':  'try',
                                   'start': start,
                                   'end':   end-4})
            # Now isolate the except and else blocks
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
            if code[pre[target]] in self.pop_jump_if and target > pos:
                self.fixed_jumps[pos] = pre[target]
                self.structs.append({'type':  'and/or',
                                       'start': start,
                                       'end':   pre[target]})
                return

            # is this an if and
            if op == self.opc.PJIF:
                match = self.rem_or(start, self.next_stmt[pos], self.opc.PJIF, target)
                ## We can't remove mid-line ifs because line structures have changed
                ## from restructBytecode().
                ##  match = self.remove_mid_line_ifs(match)
                if match:
                    if (code[pre[rtarget]] in (self.opc.JF, self.opc.JA)
                        and pre[rtarget] not in self.stmts
                        and self.restrict_to_parent(self.get_target(pre[rtarget]), parent) == rtarget):
                        if (code[pre[pre[rtarget]]] == self.opc.JA
                            and self.remove_mid_line_ifs([pos])
                            and target == self.get_target(pre[pre[rtarget]])
                            and (pre[pre[rtarget]] not in self.stmts
                            or self.get_target(pre[pre[rtarget]]) > pre[pre[rtarget]])
                            and 1 == len(self.remove_mid_line_ifs(self.rem_or(start, pre[pre[rtarget]], self.pop_jump_if, target)))):
                            pass
                        elif code[pre[pre[rtarget]]] == self.opc.RETURN_VALUE \
                                and self.remove_mid_line_ifs([pos]) \
                                and 1 == (len(set(self.remove_mid_line_ifs(self.rem_or(start, pre[pre[rtarget]],
                                                             self.pop_jump_if, target)))
                                              | set(self.remove_mid_line_ifs(self.rem_or(start, pre[pre[rtarget]],
                                                           (self.opc.PJIF, self.opc.PJIT, self.opc.JA), pre[rtarget], True))))):
                            pass
                        else:
                            fix = None
                            jump_ifs = self.all_instr(start, self.next_stmt[pos], self.opc.PJIF)
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
                elif code[next] in self.jump_forward and target == self.get_target(next):
                    if code[pre[next]] == self.opc.PJIF:
                        if code[next] == self.opc.JF or target != rtarget or code[pre[pre[rtarget]]] not in (self.opc.JA, self.opc.RETURN_VALUE):
                            self.fixed_jumps[pos] = pre[next]
                            return
                elif code[next] == self.opc.JA and code[target] in self.opc.jump_foward \
                      and self.get_target(target) == self.get_target(next):
                    self.fixed_jumps[pos] = pre[next]
                    return
            # don't add a struct for a while test, it's already taken care of
            if pos in self.ignore_if:
                return

            if code[pre[rtarget]] == self.opc.JA and pre[rtarget] in self.stmts \
                    and pre[rtarget] != pos and pre[pre[rtarget]] != pos \
                    and not (code[rtarget] == self.opc.JA and code[rtarget+3] == self.opc.POP_BLOCK and code[pre[pre[rtarget]]] != self.opc.JA):
                rtarget = pre[rtarget]
            # does the if jump just beyond a jump op, then this is probably an if statement
            if code[pre[rtarget]] in (self.opc.JA, self.opc.JF):
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

if __name__ == "__main__":
    from uncompyle6 import PYTHON_VERSION
    if PYTHON_VERSION == 2.6:
        import inspect
        co = inspect.currentframe().f_code
        tokens, customize = Scanner26(show_asm=True).disassemble(co)
    else:
        print("Need to be Python 2.6 to demo; I am %s." %
              PYTHON_VERSION)
