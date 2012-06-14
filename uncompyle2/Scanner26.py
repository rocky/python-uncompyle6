#  Copyright (c) 1999 John Aycock
#  Copyright (c) 2000-2002 by hartmut Goebel <hartmut@goebel.noris.de>
#  Copyright (c) 2005 by Dan Pascu <dan@windowmaker.org>
#
#  See main module for license.
#

__all__ = ['Token', 'Scanner', 'getscanner']

import types
import disas as dis
from collections import namedtuple
from array import array
from operator import itemgetter
from struct import *
from Scanner import Token, Code

class Scanner:
    def __init__(self, version):
        self.version = version
        self.resetTokenClass()

        dis.setVersion(version)
        globals().update({'HAVE_ARGUMENT': dis.HAVE_ARGUMENT})
        globals().update({k.replace('+','_'):v for (k,v) in dis.opmap.items()})
        globals().update({'PJIF': dis.opmap['JUMP_IF_FALSE']}) 
        globals().update({'PJIT': dis.opmap['JUMP_IF_TRUE']})
        globals().update({'JA': dis.opmap['JUMP_ABSOLUTE']})
        globals().update({'JF': dis.opmap['JUMP_FORWARD']})

        self.JUMP_OPs = map(lambda op: dis.opname[op],
                            dis.hasjrel + dis.hasjabs)        

    def setShowAsm(self, showasm, out=None):
        self.showasm = showasm
        self.out = out
            
    def setTokenClass(self, tokenClass):
        assert type(tokenClass) == types.ClassType
        self.Token = tokenClass
        
    def resetTokenClass(self):
        self.setTokenClass(Token)
        
    def disassemble(self, co, classname=None):
        """
        Disassemble a code object, returning a list of 'Token'.

        The main part of this procedure is modelled after
        dis.disassemble().
        """
        rv = []
        customize = {}
        Token = self.Token # shortcut
        self.code = array('B', co.co_code)
        n = len(self.code)
        # linestarts contains bloc code adresse (addr,block)
        self.linestarts = list(dis.findlinestarts(co))
        self.prev = [0]
        # change jump struct
        self.restructRelativeJump()

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
        # add instruction to remonde in "toDel" list
        toDel = []
        # add instruction to change in "toChange" list
        self.toChange = []
        for i in self.op_range(0, n):
            op = self.code[i]
            ret = self.getOpcodeToDel(i)
            if ret != None:
                toDel += ret
        if toDel: # degeu a revoir / repenser (tout faire d'un coup? chaud)
            toDel = sorted(list(set(toDel)))
            delta = 0
            for x in toDel:
                if self.code[x-delta] >= dis.HAVE_ARGUMENT:
                    self.code.pop(x-delta)
                    self.restructCode(x-delta)
                    self.code.pop(x-delta)
                    self.restructCode(x-delta)
                    self.code.pop(x-delta)
                    self.restructCode(x-delta)
                    delta += 3
                else:
                    self.code.pop(x-delta)
                    self.restructCode(x-delta)
                    delta += 1

        # mapping adresses of prev instru
        n = len(self.code) 
        for i in self.op_range(0, n):
            op = self.code[i]
            self.prev.append(i)
            if op >= HAVE_ARGUMENT:
                self.prev.append(i)
                self.prev.append(i)
	
        j = 0		
        linestarts = self.linestarts
        self.lines = []
        linetuple = namedtuple('linetuple', ['l_no', 'next'])
        linestartoffsets = {a for (a, _) in linestarts}
        (prev_start_byte, prev_line_no) = linestarts[0]
        for (start_byte, line_no) in linestarts[1:]:
            while j < start_byte:
                self.lines.append(linetuple(prev_line_no, start_byte))
                j += 1
            last_op = self.code[self.prev[start_byte]]
            (prev_start_byte, prev_line_no) = (start_byte, line_no)
        while j < n:
            self.lines.append(linetuple(prev_line_no, n))
            j+=1
        # self.lines contains (block,addrLastInstr)
        cf = self.find_jump_targets(self.code)
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
            op = self.code[offset]
            opname = dis.opname[op]
            oparg = None; pattr = None

            if offset in cf:
                k = 0
                for j in cf[offset]:
                    rv.append(Token('COME_FROM', None, repr(j),
                                    offset="%s_%d" % (offset, k) ))
                    k += 1
            if op >= HAVE_ARGUMENT:
                oparg = self.get_argument(offset) + extended_arg
                extended_arg = 0
                if op == dis.EXTENDED_ARG:
                    extended_arg = oparg * 65536L
                    continue
                if op in dis.hasconst:
                    const = co.co_consts[oparg]
                    if type(const) == types.CodeType:
                        oparg = const
                        if const.co_name == '<lambda>':
                            assert opname == 'LOAD_CONST'
                            opname = 'LOAD_LAMBDA'
                        elif const.co_name == '<genexpr>':
                            opname = 'LOAD_GENEXPR'
                        elif const.co_name == '<dictcomp>':
                            opname = 'LOAD_DICTCOMP'
                        elif const.co_name == '<setcomp>':
                            opname = 'LOAD_SETCOMP'
                        # verify uses 'pattr' for comparism, since 'attr'
                        # now holds Code(const) and thus can not be used
                        # for comparism (todo: think about changing this)
                        #pattr = 'code_object @ 0x%x %s->%s' %\
                        #	(id(const), const.co_filename, const.co_name)
                        pattr = '<code_object ' + const.co_name + '>'
                    else:
                        pattr = const
                elif op in dis.hasname:
                    pattr = names[oparg]
                elif op in dis.hasjrel:
                    pattr = repr(offset + 3 + oparg)
                elif op in dis.hasjabs:
                    pattr = repr(oparg)
                elif op in dis.haslocal:
                    pattr = varnames[oparg]
                elif op in dis.hascompare:
                    pattr = dis.cmp_op[oparg]
                elif op in dis.hasfree:
                    pattr = free[oparg]
            if offset in self.toChange:
                if self.code[offset] == JA and self.code[oparg] == WITH_CLEANUP:
                    opname = 'SETUP_WITH'
                    cf[oparg] = cf.get(oparg, []) + [offset]
            if op in (BUILD_LIST, BUILD_TUPLE, BUILD_SLICE,
                            UNPACK_SEQUENCE,
                            MAKE_FUNCTION, CALL_FUNCTION, MAKE_CLOSURE,
                            CALL_FUNCTION_VAR, CALL_FUNCTION_KW,
                            CALL_FUNCTION_VAR_KW, DUP_TOPX,
                            ):
                # CE - Hack for >= 2.5
                #      Now all values loaded via LOAD_CLOSURE are packed into
                #      a tuple before calling MAKE_CLOSURE.
                if op == BUILD_TUPLE and \
                    self.code[offset-3] == LOAD_CLOSURE:
                    continue
                else:
                    opname = '%s_%d' % (opname, oparg)
                    if op != BUILD_SLICE:
                        customize[opname] = oparg
            elif op == JA:
                target = self.get_target(offset)
                if target < offset:
                    if offset in self.stmts and self.code[offset+3] not in (END_FINALLY, POP_BLOCK) \
                     and offset not in self.not_continue:
                        opname = 'CONTINUE'
                    else:
                        opname = 'JUMP_BACK'

            elif op == LOAD_GLOBAL:
                try:
                    if pattr == 'AssertionError' and rv and rv[-1] == 'JUMP_IF_TRUE':
                        opname = 'LOAD_ASSERT'
                except AttributeError:
                    pass
            elif op == RETURN_VALUE:
                if offset in self.return_end_ifs:
                    opname = 'RETURN_END_IF'

            if offset not in replace:
                rv.append(Token(opname, oparg, pattr, offset, linestart = offset in linestartoffsets))
            else:
                rv.append(Token(replace[offset], oparg, pattr, offset, linestart = offset in linestartoffsets))
		
        if self.showasm:
            out = self.out # shortcut
            for t in rv:
                print >>out, t
            print >>out
        return rv, customize

    def getOpcodeToDel(self, i):
        """
        check validity of the opcode at position I and return a list of opcode to delete
        """
        opcode = self.code[i]
        opsize = self.op_size(opcode)
		
        if i+opsize >= len(self.code):
            return None

        if opcode == EXTENDED_ARG:
            raise 'TODO'
        # del POP_TOP
        if opcode in (PJIF,PJIT,JA,JF,RETURN_VALUE):
            if self.code[i+opsize] == POP_TOP:
                if self.code[i+opsize] == self.code[i+opsize+1] and self.code[i+opsize] == self.code[i+opsize+2] \
                and opcode in (JF,JA) and self.code[i+opsize] != self.code[i+opsize+3]:
                    pass
                else:
                    return [i+opsize]
        if opcode == RAISE_VARARGS:
            if self.code[i+opsize] == POP_TOP:
                return [i+opsize]
        if opcode == BUILD_LIST:
            if self.code[i+opsize] == DUP_TOP and self.code[i+opsize+1] in (STORE_NAME,STORE_FAST):
                # del DUP/STORE_NAME x
                toDel = [i+opsize,i+opsize+1]
                nameDel = self.get_argument(i+opsize+1)
                start = i+opsize+1
                end = start	
                # del LOAD_NAME x
                while end < len(self.code):
                    end = self.first_instr(end, len(self.code), (LOAD_NAME,LOAD_FAST))
                    if nameDel == self.get_argument(end):
                        toDel += [end]
                        break
                    if self.code[end] == LOAD_NAME:
                        end += self.op_size(LOAD_NAME)
                    else:
                        end += self.op_size(LOAD_FAST)
                # log JA/POP_TOP to del and update PJIF
                while start < end:
                    start = self.first_instr(start, len(self.code), (PJIF,PJIT))
                    if start == None: break
                    target = self.get_target(start)
                    if self.code[target] == POP_TOP and self.code[target-3] == JA:
                        toDel += [target, target-3]
                        # update PJIF
                        target = self.get_target(target-3)
                        if target > 0xFFFF:
                            raise 'TODO'
                        self.code[start+1] = target & 0xFF
                        self.code[start+2] = (target >> 8) & 0xFF
                    start += self.op_size(PJIF)	
                # del DELETE_NAME x 
                start = end
                while end < len(self.code):
                    end = self.first_instr(end, len(self.code), (DELETE_NAME,DELETE_FAST))
                    if nameDel == self.get_argument(end):
                        toDel += [end]
                        break
                    if self.code[end] == DELETE_NAME:
                        end += self.op_size(DELETE_NAME)
                    else:
                        end += self.op_size(DELETE_FAST)
                return toDel
        # change join(for..) struct
        if opcode == SETUP_LOOP:
            if self.code[i+3] == LOAD_FAST and self.code[i+6] == FOR_ITER: 
                end = self.first_instr(i, len(self.code), RETURN_VALUE)
                end = self.first_instr(i, end, YIELD_VALUE)
                if end and self.code[end+1] == POP_TOP and self.code[end+2] == JA and self.code[end+5] == POP_BLOCK:
                    return [i,end+5]
        # with stmt
        if opcode == WITH_CLEANUP:
            allRot = self.all_instr(0, i, (ROT_TWO))
            chckRot = -1
            for rot in allRot:
                if self.code[rot+1] == LOAD_ATTR and self.code[rot-3] == LOAD_ATTR \
                    and self.code[rot-4] == DUP_TOP:
                    chckRot = rot
            assert chckRot > 0
            toDel = [chckRot-4,chckRot-3,chckRot]
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
            if self.code[chckStp-3] in (STORE_NAME,STORE_FAST) and self.code[chckStp+3] in (LOAD_NAME,LOAD_FAST) \
                and self.code[chckStp+6] in (DELETE_NAME,DELETE_FAST):
                toDel += [chckStp-3,chckStp+3,chckStp+6]
            # SETUP_WITH opcode dosen't exist in 2.6 but is necessary for the grammar
            self.code[chckRot+1] = JUMP_ABSOLUTE # ugly hack
            self.code[chckRot+2] = i & 0xFF
            self.code[chckRot+3] = (i >> 8) & 0xFF
            self.toChange.append(chckRot+1)
            return toDel
        return None
		
    def restructRelativeJump(self):
        """
        change relative JUMP_IF_FALSE/TRUE to absolut jump
		and remap the target of PJIF/PJIT
        """
        for i in self.op_range(0, len(self.code)):
            if(self.code[i] in (PJIF,PJIT)):
                target = self.get_argument(i)
                target += i + 3
                if target > 0xFFFF:
                    raise 'A gerer'
                self.code[i+1] = target & 0xFF
                self.code[i+2] = (target >> 8) & 0xFF

        for i in self.op_range(0, len(self.code)):
            if(self.code[i] in (PJIF,PJIT)):
                target = self.get_target(i)
                if self.code[target] == JA:
                    target = self.get_target(target)
                    if target > 0xFFFF:
                        raise 'A gerer'
                    self.code[i+1] = target & 0xFF
                    self.code[i+2] = (target >> 8) & 0xFF
		
    def restructCode(self, i):
        """
        restruct linestarts and jump destination after removing a POP_TOP
        """
        result = list()
        for item in self.linestarts:
            if i < item[0]:	
                result.append((item[0]-1, item[1]))
            else:
                result.append((item[0], item[1]))
        self.linestarts = result

        for change in self.toChange:
            if change > i:
                self.toChange[self.toChange.index(change)] -= 1
        for x in self.op_range(0, len(self.code)):
            op = self.code[x]
            if op >= HAVE_ARGUMENT:
                if op in dis.hasjrel:
                    if x < i and self.get_target(x) > i:
                        if self.code[x+1]-1 < 0:
                            self.code[x+2] -= 1
                            self.code[x+1] = self.code[x+1]+255
                        else:
                            self.code[x+1] -= 1
                elif op in dis.hasjabs:
                    if i < self.get_target(x):
                        if self.code[x+1]-1 < 0:
                            self.code[x+2] -= 1
                            self.code[x+1] = self.code[x+1]+255
                        else:
                            self.code[x+1] -= 1
    	
    def get_target(self, pos, op=None):
        if op is None:
            op = self.code[pos]
        target = self.get_argument(pos)
        if op in dis.hasjrel:
            target += pos + 3
        return target

    def get_argument(self, pos):
        target = self.code[pos+1] + self.code[pos+2] * 256
        return target
		
    def first_instr(self, start, end, instr, target=None, exact=True):
        """
        Find the first <instr> in the block from start to end.
        <instr> is any python bytecode instruction or a list of opcodes
        If <instr> is an opcode with a target (like a jump), a target
        destination can be specified which must match precisely if exact
        is True, or if exact is False, the instruction which has a target
        closest to <target> will be returned.

        Return index to it or None if not found.
        """
        code = self.code
        assert(start>=0 and end<=len(code))

        try:    None in instr
        except: instr = [instr]

        pos = None
        distance = len(code)
        for i in self.op_range(start, end):
            op = code[i]
            if op in instr:
                if target is None:
                    return i
                dest = self.get_target(i, op)
                if dest == target:
                    return i
                elif not exact:
                    _distance = abs(target - dest)
                    if _distance < distance:
                        distance = _distance
                        pos = i
        return pos

    def last_instr(self, start, end, instr, target=None, exact=True):
        """
        Find the last <instr> in the block from start to end.
        <instr> is any python bytecode instruction or a list of opcodes
        If <instr> is an opcode with a target (like a jump), a target
        destination can be specified which must match precisely if exact
        is True, or if exact is False, the instruction which has a target
        closest to <target> will be returned.

        Return index to it or None if not found.
        """

        code = self.code
        if not (start>=0 and end<=len(code)):
            return None

        try:    None in instr
        except: instr = [instr]

        pos = None
        distance = len(code)
        for i in self.op_range(start, end):
            op = code[i]
            if op in instr:
                if target is None:
                    pos = i
                else:
                    dest = self.get_target(i, op)
                    if dest == target:
                        distance = 0
                        pos = i
                    elif not exact:
                        _distance = abs(target - dest)
                        if _distance <= distance:
                            distance = _distance
                            pos = i
        return pos

    def all_instr(self, start, end, instr, target=None, include_beyond_target=False):
        """
        Find all <instr> in the block from start to end.
        <instr> is any python bytecode instruction or a list of opcodes
        If <instr> is an opcode with a target (like a jump), a target
        destination can be specified which must match precisely.

        Return a list with indexes to them or [] if none found.
        """
        
        code = self.code
        assert(start>=0 and end<=len(code))

        try:    None in instr
        except: instr = [instr]

        result = []
        for i in self.op_range(start, end):
            op = code[i]
            if op in instr:
                if target is None:
                    result.append(i)
                else:
                    t = self.get_target(i, op)
                    if include_beyond_target and t >= target:
                        result.append(i)
                    elif t == target:
                        result.append(i)
        return result

    def op_size(self, op):
        if op < HAVE_ARGUMENT:
            return 1
        else:
            return 3
            
    def op_range(self, start, end):
        while start < end:
            yield start
            start += self.op_size(self.code[start])

    def build_stmt_indices(self):
        code = self.code
        start = 0;
        end = len(code)

        stmt_opcodes = {
            SETUP_LOOP, BREAK_LOOP, CONTINUE_LOOP,
            SETUP_FINALLY, END_FINALLY, SETUP_EXCEPT,
            POP_BLOCK, STORE_FAST, DELETE_FAST, STORE_DEREF,
            STORE_GLOBAL, DELETE_GLOBAL, STORE_NAME, DELETE_NAME,
            STORE_ATTR, DELETE_ATTR, STORE_SUBSCR, DELETE_SUBSCR,
            RETURN_VALUE, RAISE_VARARGS, POP_TOP,
            PRINT_EXPR, PRINT_ITEM, PRINT_NEWLINE, PRINT_ITEM_TO, PRINT_NEWLINE_TO,
            JUMP_ABSOLUTE, EXEC_STMT,
        }

        stmt_opcode_seqs = [(PJIF, JF), (PJIF, JA), (PJIT, JF), (PJIT, JA)]
        
        designator_ops = {
            STORE_FAST, STORE_NAME, STORE_GLOBAL, STORE_DEREF, STORE_ATTR, 
            STORE_SLICE_0, STORE_SLICE_1, STORE_SLICE_2, STORE_SLICE_3,
            STORE_SUBSCR, UNPACK_SEQUENCE, JA
        }

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
                if code[j] == LIST_APPEND: #list comprehension
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
        slist += [len(code)] * (len(code)-len(slist))
               
    def remove_mid_line_ifs(self, ifs):
        filtered = []
        for i in ifs:
            if self.lines[i].l_no == self.lines[i+3].l_no:
                if self.code[self.prev[self.lines[i].next]] in (PJIT, PJIF):
                    continue
            filtered.append(i)
        return filtered

    
    def rem_or(self, start, end, instr, target=None, include_beyond_target=False):
        """
        Find all <instr> in the block from start to end.
        <instr> is any python bytecode instruction or a list of opcodes
        If <instr> is an opcode with a target (like a jump), a target
        destination can be specified which must match precisely.

        Return a list with indexes to them or [] if none found.
        """
        
        code = self.code
        assert(start>=0 and end<=len(code))

        try:    None in instr
        except: instr = [instr]

        result = []
        for i in self.op_range(start, end):
            op = code[i]
            if op in instr:
                if target is None:
                    result.append(i)
                else:
                    t = self.get_target(i, op)
                    if include_beyond_target and t >= target:
                        result.append(i)
                    elif t == target:
                        result.append(i)
                        
        pjits = self.all_instr(start, end, PJIT)
        filtered = []
        for pjit in pjits:
            tgt = self.get_target(pjit)-3
            for i in result:
                if i <= pjit or i >= tgt:
                    filtered.append(i)
            result = filtered
            filtered = []
        return result

    def next_except_jump(self, start):
        """
        Return the next jump that was generated by an except SomeException:
        construct in a try...except...else clause or None if not found.
        """
        except_match = self.first_instr(start, self.lines[start].next, (PJIF))
        if except_match:
            jmp = self.prev[self.get_target(except_match)]
            self.ignore_if.add(except_match)
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
                    return self.prev[i]
                count_END_FINALLY += 1
            elif op in (SETUP_EXCEPT, SETUP_FINALLY):
                count_SETUP_ += 1
        #return self.lines[start].next

    def restrict_to_parent(self, target, parent):
        """Restrict pos to parent boundaries."""
        if not (parent['start'] < target < parent['end']):
            target = parent['end']
        return target
        
    def detect_structure(self, pos, op=None):
        """
        Detect type of block structures and their boundaries to fix optimizied jumps
        in python2.3+
        """

        # TODO: check the struct boundaries more precisely -Dan

        code = self.code
        # Ev remove this test and make op a mandatory argument -Dan
        if op is None:
            op = code[pos]

        ## Detect parent structure
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
        ## We need to know how many new structures were added in this run
        origStructCount = len(self.structs)

        if op == SETUP_LOOP:
            #import pdb; pdb.set_trace()
            start = pos+3
            target = self.get_target(pos, op)
            end    = self.restrict_to_parent(target, parent)

            if target != end:
                self.fixed_jumps[pos] = end
            
            (line_no, next_line_byte) = self.lines[pos]
            jump_back = self.last_instr(start, end, JA,
                                          next_line_byte, False)
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
                    else:
                        self.ignore_if.add(test)
                        test_target = self.get_target(test)
                        if test_target > (jump_back+3):
                            jump_back = test_target
                 
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
                #print target, end, parent
            ## Add the try block
            self.structs.append({'type':  'try',
                                   'start': start,
                                   'end':   end-4})
            ## Now isolate the except and else blocks
            end_else = start_else = self.get_target(self.prev[end])

            ## Add the except blocks
            i = end
            while self.code[i] != END_FINALLY:
                jmp = self.next_except_jump(i)
                if jmp == None: # check
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
                        #self.fixed_jumps[i] = jmp
						self.fixed_jumps[jmp] = -1
                    self.structs.append({'type':  'except',
                                   'start': i,
                                   'end':   jmp})
                    i = jmp + 3   

            ## Add the try-else block
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
            #does this jump to right after another cond jump?
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
                                and 1 == (len(set(self.remove_mid_line_ifs(self.rem_or(start, pre[pre[rtarget]], \
                                                             (PJIF, PJIT), target))) \
                                              | set(self.remove_mid_line_ifs(self.rem_or(start, pre[pre[rtarget]], \
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
            #don't add a struct for a while test, it's already taken care of
            if pos in self.ignore_if:
                return
 
            if code[pre[rtarget]] == JA and pre[rtarget] in self.stmts \
                    and pre[rtarget] != pos and pre[pre[rtarget]] != pos \
                    and not (code[rtarget] == JA and code[rtarget+3] == POP_BLOCK and code[pre[pre[rtarget]]] != JA):
                rtarget = pre[rtarget]
            #does the if jump just beyond a jump op, then this is probably an if statement
            if code[pre[rtarget]] in (JA, JF):
                if_end = self.get_target(pre[rtarget])
                
                #is this a loop not an if?
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
            # if it's an old JUMP_IF_FALSE_OR_POP, JUMP_IF_TRUE_OR_POP
            #if target > pos:
            #    unop_target = self.last_instr(pos, target, JF, target)
            #    if unop_target and code[unop_target+3] != ROT_TWO:
            #        self.fixed_jumps[pos] = unop_target
            #    else:
            #        self.fixed_jumps[pos] = self.restrict_to_parent(target, parent)

    def find_jump_targets(self, code):
        """
        Detect all offsets in a byte code which are jump targets.

        Return the list of offsets.

        This procedure is modelled after dis.findlables(), but here
        for each target the number of jumps are counted.
        """

        hasjrel = dis.hasjrel
        hasjabs = dis.hasjabs

        n = len(code)
        self.structs = [{'type':  'root',
                           'start': 0,
                           'end':   n-1}]
        self.loops = []  ## All loop entry points
        self.fixed_jumps = {} ## Map fixed jumps to their real destination
        self.ignore_if = set()
        self.build_stmt_indices() 
        self.not_continue = set()
        self.return_end_ifs = set()

        targets = {}
        for i in self.op_range(0, n):
            op = code[i]

            ## Determine structures and fix jumps for 2.3+
            self.detect_structure(i, op)

            if op >= HAVE_ARGUMENT:
                label = self.fixed_jumps.get(i)
                oparg = self.get_argument(i)  
                if label is None:
                    if op in hasjrel and op != FOR_ITER:
                        label = i + 3 + oparg
                    #elif op in hasjabs: Pas de gestion des jump abslt
                        #if op in (PJIF, PJIT): Or pop a faire
                            #if (oparg > i):
                                #label = oparg
                if label is not None and label != -1:
                    targets[label] = targets.get(label, []) + [i]
            elif op == END_FINALLY and i in self.fixed_jumps:
                label = self.fixed_jumps[i]
                targets[label] = targets.get(label, []) + [i]
        return targets

