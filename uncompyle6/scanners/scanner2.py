# Copyright (c) 2015, 2016 by Rocky Bernstein
# Copyright (c) 2005 by Dan Pascu <dan@windowmaker.org>
# Copyright (c) 2000-2002 by hartmut Goebel <h.goebel@crazy-compilers.com>
"""
Python 2 Generic bytecode scanner/deparser

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

from uncompyle6 import PYTHON_VERSION

if PYTHON_VERSION < 2.6:
    from xdis.namedtuple25 import namedtuple
else:
    from collections import namedtuple

from array import array

from uncompyle6.scanner import op_has_argument
from xdis.code import iscode

import uncompyle6.scanner as scan

class Scanner2(scan.Scanner):
    def __init__(self, version, show_asm=None, is_pypy=False):
        scan.Scanner.__init__(self, version, show_asm, is_pypy)
        self.pop_jump_if = frozenset([self.opc.PJIF, self.opc.PJIT])
        self.jump_forward = frozenset([self.opc.JUMP_ABSOLUTE, self.opc.JUMP_FORWARD])
        # This is the 2.5+ default
        # For <2.5 it is <generator expression>
        self.genexpr_name = '<genexpr>'

    @staticmethod
    def unmangle_name(name, classname):
        """Remove __ from the end of _name_ if it starts with __classname__
        return the "unmangled" name.
        """
        if name.startswith(classname) and name[-2:] != '__':
            return name[len(classname) - 2:]
        return name

    @classmethod
    def unmangle_code_names(self, co, classname):
        """Remove __ from the end of _name_ if it starts with __classname__
        return the "unmangled" name.
        """
        if classname:
            classname = '_' + classname.lstrip('_') + '__'

            free = [ self.unmangle_name(name, classname)
                     for name in (co.co_cellvars + co.co_freevars) ]
            names = [ self.unmangle_name(name, classname)
                      for name in co.co_names ]
            varnames = [ self.unmangle_name(name, classname)
                         for name in co.co_varnames ]
        else:
            free = co.co_cellvars + co.co_freevars
            names = co.co_names
            varnames = co.co_varnames
        return free, names, varnames

    def ingest(self, co, classname=None, code_objects={}, show_asm=None):
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

        if not show_asm:
            show_asm = self.show_asm

        # show_asm = 'after'
        if show_asm in ('both', 'before'):
            from xdis.bytecode import Bytecode
            bytecode = Bytecode(co, self.opc)
            for instr in bytecode.get_instructions(co):
                print(instr._disassemble())

        # Container for tokens
        tokens = []

        customize = {}
        if self.is_pypy:
            customize['PyPy'] = 1

        Token = self.Token # shortcut

        codelen = self.setup_code(co)

        self.build_lines_data(co, codelen)
        self.build_prev_op(codelen)

        free, names, varnames = self.unmangle_code_names(co, classname)
        self.names = names

        # Scan for assertions. Later we will
        # turn 'LOAD_GLOBAL' to 'LOAD_ASSERT'.
        # 'LOAD_ASSERT' is used in assert statements.
        self.load_asserts = set()
        for i in self.op_range(0, codelen):
            # We need to detect the difference between:
            #   raise AssertionError
            #  and
            #   assert ...
            # Below we use the heuristic that it is preceded by a POP_JUMP.
            # however we could also use followed by RAISE_VARARGS
            # or for PyPy there may be a JUMP_IF_NOT_DEBUG before.
            # FIXME: remove uses of PJIF, and PJIT
            if self.is_pypy:
                have_pop_jump = self.code[i] in (self.opc.PJIF,
                                                 self.opc.PJIT)
            else:
                have_pop_jump = self.code[i] == self.opc.PJIT

            if have_pop_jump and self.code[i+3] == self.opc.LOAD_GLOBAL:
                if names[self.get_argument(i+3)] == 'AssertionError':
                    self.load_asserts.add(i+3)

        jump_targets = self.find_jump_targets(show_asm)
        # contains (code, [addrRefToCode])

        last_stmt = self.next_stmt[0]
        i = self.next_stmt[last_stmt]
        replace = {}
        while i < codelen - 1:
            if self.lines[last_stmt].next > i:
                # Distinguish "print ..." from "print ...,"
                if self.code[last_stmt] == self.opc.PRINT_ITEM:
                    if self.code[i] == self.opc.PRINT_ITEM:
                        replace[i] = 'PRINT_ITEM_CONT'
                    elif self.code[i] == self.opc.PRINT_NEWLINE:
                        replace[i] = 'PRINT_NEWLINE_CONT'
            last_stmt = i
            i = self.next_stmt[i]

        extended_arg = 0
        for offset in self.op_range(0, codelen):
            if offset in jump_targets:
                jump_idx = 0
                # We want to process COME_FROMs to the same offset to be in *descending*
                # offset order so we have the larger range or biggest instruction interval
                # last. (I think they are sorted in increasing order, but for safety
                # we sort them). That way, specific COME_FROM tags will match up
                # properly. For example, a "loop" with an "if" nested in it should have the
                # "loop" tag last so the grammar rule matches that properly.
                # last_offset = -1
                for jump_offset  in sorted(jump_targets[offset], reverse=True):
                    # if jump_offset == last_offset:
                    #     continue
                    # last_offset = jump_offset
                    come_from_name = 'COME_FROM'
                    op_name = self.opc.opname[self.code[jump_offset]]
                    if op_name.startswith('SETUP_') and self.version == 2.7:
                        come_from_type = op_name[len('SETUP_'):]
                        if come_from_type not in ('LOOP', 'EXCEPT'):
                            come_from_name = 'COME_FROM_%s' % come_from_type
                        pass
                    tokens.append(Token(
                        come_from_name, None, repr(jump_offset),
                        offset="%s_%d" % (offset, jump_idx),
                        has_arg = True))
                    jump_idx += 1
                    pass

            op = self.code[offset]
            op_name = self.opc.opname[op]

            oparg = None; pattr = None
            has_arg = op_has_argument(op, self.opc)
            if has_arg:
                oparg = self.get_argument(offset) + extended_arg
                extended_arg = 0
                if op == self.opc.EXTENDED_ARG:
                    extended_arg = oparg * scan.L65536
                    continue
                if op in self.opc.hasconst:
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
                elif op in self.opc.hasname:
                    pattr = names[oparg]
                elif op in self.opc.hasjrel:
                    #  use instead: hasattr(self, 'patch_continue'): ?
                    if self.version == 2.7:
                        self.patch_continue(tokens, offset, op)
                    pattr = repr(offset + 3 + oparg)
                elif op in self.opc.hasjabs:
                    # use instead: hasattr(self, 'patch_continue'): ?
                    if self.version == 2.7:
                        self.patch_continue(tokens, offset, op)
                    pattr = repr(oparg)
                elif op in self.opc.haslocal:
                    pattr = varnames[oparg]
                elif op in self.opc.hascompare:
                    pattr = self.opc.cmp_op[oparg]
                elif op in self.opc.hasfree:
                    pattr = free[oparg]

            if op in self.varargs_ops:
                # CE - Hack for >= 2.5
                #      Now all values loaded via LOAD_CLOSURE are packed into
                #      a tuple before calling MAKE_CLOSURE.
                if op == self.opc.BUILD_TUPLE and \
                    self.code[self.prev[offset]] == self.opc.LOAD_CLOSURE:
                    continue
                else:
                    if self.is_pypy and not oparg and op_name == 'BUILD_MAP':
                        op_name = 'BUILD_MAP_n'
                    else:
                        op_name = '%s_%d' % (op_name, oparg)
                    if op != self.opc.BUILD_SLICE:
                        customize[op_name] = oparg
            elif self.is_pypy and op_name in ('LOOKUP_METHOD',
                                             'JUMP_IF_NOT_DEBUG',
                                             'SETUP_EXCEPT',
                                             'SETUP_FINALLY'):
                # The value in the dict is in special cases in semantic actions, such
                # as CALL_FUNCTION. The value is not used in these cases, so we put
                # in arbitrary value 0.
                customize[op_name] = 0
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
                target = self.get_target(offset)
                if target <= offset:
                    if (offset in self.stmts
                        and self.code[offset+3] not in (self.opc.END_FINALLY,
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
                tokens.append(Token(
                    op_name, oparg, pattr, offset, linestart, op,
                    has_arg, self.opc))
            else:
                tokens.append(Token(
                    replace[offset], oparg, pattr, offset, linestart,
                    op, has_arg, self.opc))
                pass
            pass

        if show_asm in ('both', 'after'):
            for t in tokens:
                print(t.format(line_prefix='L.'))
            print()
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
            if self.code[i] in (self.opc.RETURN_VALUE, self.opc.END_FINALLY):
                n = i + 1
                pass
            pass
        assert n > -1, "Didn't find RETURN_VALUE or END_FINALLY"
        self.code = array('B', co.co_code[:n])

        return n

    def build_prev_op(self, n):
        self.prev = [0]
        # mapping addresses of instruction & argument
        for i in self.op_range(0, n):
            op = self.code[i]
            self.prev.append(i)
            if self.op_hasArgument(op):
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

        # self.linestarts is a tuple of (offset, line number).
        # Turn that in a has that we can index
        self.linestarts = list(self.opc.findlinestarts(co))
        self.linestartoffsets = {}
        for offset, lineno in self.linestarts:
            self.linestartoffsets[offset] = lineno

        j = 0
        (prev_start_byte, prev_line_no) = self.linestarts[0]
        for (start_byte, line_no) in self.linestarts[1:]:
            while j < start_byte:
                self.lines.append(linetuple(prev_line_no, start_byte))
                j += 1
            prev_line_no = start_byte
        while j < n:
            self.lines.append(linetuple(prev_line_no, n))
            j+=1
        return

    def build_statement_indices(self):
        code = self.code
        start = 0
        end = len(code)

        stmt_opcode_seqs = frozenset([(self.opc.PJIF, self.opc.JUMP_FORWARD),
                                      (self.opc.PJIF, self.opc.JUMP_ABSOLUTE),
                                      (self.opc.PJIT, self.opc.JUMP_FORWARD),
                                      (self.opc.PJIT, self.opc.JUMP_ABSOLUTE)])

        prelim = self.all_instr(start, end, self.stmt_opcodes)

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
            if code[s] == self.opc.JUMP_ABSOLUTE and s not in pass_stmts:
                target = self.get_target(s)
                if target > s or self.lines[last_stmt].l_no == self.lines[s].l_no:
                    stmts.remove(s)
                    continue
                j = self.prev[s]
                while code[j] == self.opc.JUMP_ABSOLUTE:
                    j = self.prev[j]
                if (self.version >= 2.3 and
                    self.opc.opname[code[j]] == 'LIST_APPEND'): # list comprehension
                    stmts.remove(s)
                    continue
            elif code[s] == self.opc.POP_TOP:
                # The POP_TOP in:
                #   ROT_TWO, POP_TOP,
                #   RETURN_xxx, POP_TOP (in 2.6-), or
                #   JUMP_IF_{FALSE,TRUE}, POP_TOP  (in 2.6-)
                # is part of the previous instruction and not the
                # beginning of a new statement
                prev = code[self.prev[s]]
                if (prev == self.opc.ROT_TWO or
                    self.version < 2.7 and prev in
                    (self.opc.JUMP_IF_FALSE, self.opc.JUMP_IF_TRUE,
                     self.opc.RETURN_VALUE)):
                    stmts.remove(s)
                    continue
            elif code[s] in self.designator_ops:
                j = self.prev[s]
                while code[j] in self.designator_ops:
                    j = self.prev[j]
                if self.version >= 2.1 and code[j] == self.opc.FOR_ITER:
                    stmts.remove(s)
                    continue
            last_stmt = s
            slist += [s] * (s-i)
            i = s
        slist += [end] * (end-len(slist))

    def next_except_jump(self, start):
        """
        Return the next jump that was generated by an except SomeException:
        construct in a try...except...else clause or None if not found.
        """

        if self.code[start] == self.opc.DUP_TOP:
            except_match = self.first_instr(start, len(self.code), self.opc.PJIF)
            if except_match:
                jmp = self.prev[self.get_target(except_match)]

                # In Python < 2.7 we may have jumps to jumps
                if self.version < 2.7 and self.code[jmp] in self.jump_forward:
                    self.not_continue.add(jmp)
                    jmp = self.get_target(jmp)
                    prev_offset = self.prev[except_match]
                    # COMPARE_OP argument should be "exception match" or 10
                    if (self.code[prev_offset] == self.opc.COMPARE_OP and
                        self.code[prev_offset+1] != 10):
                        return None
                    if jmp not in self.pop_jump_if | self.jump_forward:
                        self.ignore_if.add(except_match)
                        return None

                self.ignore_if.add(except_match)
                self.not_continue.add(jmp)
                return jmp

        count_END_FINALLY = 0
        count_SETUP_ = 0
        for i in self.op_range(start, len(self.code)):
            op = self.code[i]
            if op == self.opc.END_FINALLY:
                if count_END_FINALLY == count_SETUP_:
                    if self.version == 2.7:
                        assert self.code[self.prev[i]] in \
                            self.jump_forward | frozenset([self.opc.RETURN_VALUE])
                    self.not_continue.add(self.prev[i])
                    return self.prev[i]
                count_END_FINALLY += 1
            elif op in self.setup_ops:
                count_SETUP_ += 1

    def detect_control_flow(self, offset, op):
        """
        Detect type of block structures and their boundaries to fix optimized jumps
        in python2.3+
        """

        # TODO: check the struct boundaries more precisely -Dan

        code = self.code

        # Detect parent structure
        parent = self.structs[0]
        start  = parent['start']
        end    = parent['end']
        for struct in self.structs:
            _start = struct['start']
            _end   = struct['end']
            if (_start <= offset < _end) and (_start >= start and _end <= end):
                start  = _start
                end    = _end
                parent = struct

        if op == self.opc.SETUP_LOOP:

            # We categorize loop types: 'for', 'while', 'while 1' with
            # possibly suffixes '-loop' and '-else'
            # Try to find the jump_back instruction of the loop.
            # It could be a return instruction.

            start = offset+3
            target = self.get_target(offset, op)
            end    = self.restrict_to_parent(target, parent)
            self.setup_loop_targets[offset] = target
            self.setup_loops[target] = offset

            if target != end:
                self.fixed_jumps[offset] = end

            (line_no, next_line_byte) = self.lines[offset]
            jump_back = self.last_instr(start, end, self.opc.JUMP_ABSOLUTE,
                                        next_line_byte, False)

            if jump_back:
                # Account for the fact that < 2.7 has an explicit
                # POP_TOP instruction in the equivalate POP_JUMP_IF
                # construct
                if self.version < 2.7:
                    jump_forward_offset = jump_back+4
                    return_val_offset1 = self.prev[self.prev[self.prev[end]]]
                    # Is jump back really "back"?
                    jump_target = self.get_target(jump_back, code[jump_back])
                    if (jump_target > jump_back or
                        code[jump_back+3] in [self.opc.JUMP_FORWARD, self.opc.JUMP_ABSOLUTE]):
                        jump_back = None
                        pass
                else:
                    jump_forward_offset = jump_back+3
                    return_val_offset1 = self.prev[self.prev[end]]

            if (jump_back and jump_back != self.prev[end]
                and code[jump_forward_offset] in self.jump_forward):
                if (code[self.prev[end]] == self.opc.RETURN_VALUE or
                    (code[self.prev[end]] == self.opc.POP_BLOCK
                     and code[return_val_offset1] == self.opc.RETURN_VALUE)):
                    jump_back = None
            if not jump_back:
                # loop suite ends in return
                # scanner26 of wbiti had:
                # jump_back = self.last_instr(start, end, self.opc.JUMP_ABSOLUTE, start, False)
                jump_back = self.last_instr(start, end, self.opc.RETURN_VALUE)
                if not jump_back:
                    return
                jump_back += 1

                if_offset = None
                if self.version < 2.7:
                    # Look for JUMP_IF POP_TOP ...
                    if (code[self.prev[next_line_byte]] == self.opc.POP_TOP
                        and (code[self.prev[self.prev[next_line_byte]]]
                             in self.pop_jump_if)):
                        if_offset = self.prev[self.prev[next_line_byte]]
                elif code[self.prev[next_line_byte]] in self.pop_jump_if:
                    # Look for POP_JUMP_IF ...
                    if_offset = self.prev[next_line_byte]
                if if_offset:
                    loop_type = 'while'
                    self.ignore_if.add(if_offset)
                    if self.version < 2.7 and (
                            code[self.prev[jump_back]] == self.opc.RETURN_VALUE):
                        self.ignore_if.add(self.prev[jump_back])
                        pass
                    pass
                else:
                    loop_type = 'for'
                target = next_line_byte
                end = jump_back + 3
            else:
                if self.get_target(jump_back) >= next_line_byte:
                    jump_back = self.last_instr(start, end, self.opc.JUMP_ABSOLUTE, start, False)
                if end > jump_back+4 and code[end] in self.jump_forward:
                    if code[jump_back+4] in self.jump_forward:
                        if self.get_target(jump_back+4) == self.get_target(end):
                            self.fixed_jumps[offset] = jump_back+4
                            end = jump_back+4
                elif target < offset:
                    self.fixed_jumps[offset] = jump_back+4
                    end = jump_back+4

                target = self.get_target(jump_back, self.opc.JUMP_ABSOLUTE)

                if (self.version >= 2.0 and
                    code[target] in (self.opc.FOR_ITER, self.opc.GET_ITER)):
                    loop_type = 'for'
                else:
                    loop_type = 'while'
                    if (self.version < 2.7
                        and self.code[self.prev[next_line_byte]] == self.opc.POP_TOP):
                        test = self.prev[self.prev[next_line_byte]]
                    else:
                        test = self.prev[next_line_byte]

                    if test == offset:
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
            start  = offset+3
            target = self.get_target(offset, op)
            end    = self.restrict_to_parent(target, parent)
            if target != end:
                self.fixed_jumps[offset] = end
                # print target, end, parent
            # Add the try block
            self.structs.append({'type':  'try',
                                   'start': start-3,
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
                    target = self.get_target(jmp)
                    if target != start_else:
                        end_else = self.get_target(jmp)
                    if self.code[jmp] == self.opc.JUMP_FORWARD:
                        if self.version <= 2.6:
                            self.fixed_jumps[jmp] = target
                        else:
                            self.fixed_jumps[jmp] = -1
                    self.structs.append({'type':  'except',
                                   'start': i,
                                   'end':   jmp})
                    i = jmp + 3

            # Add the try-else block
            if end_else != start_else:
                r_end_else = self.restrict_to_parent(end_else, parent)
                # May be able to drop the 2.7 test.
                if self.version == 2.7:
                    self.structs.append({'type':  'try-else',
                                           'start': i+1,
                                           'end':   r_end_else})
                    self.fixed_jumps[i] = r_end_else
            else:
                self.fixed_jumps[i] = i+1

        elif op in self.pop_jump_if:
            target = self.get_target(offset, op)
            rtarget = self.restrict_to_parent(target, parent)

            # Do not let jump to go out of parent struct bounds
            if target != rtarget and parent['type'] == 'and/or':
                self.fixed_jumps[offset] = rtarget
                return

            jump_if_offset = offset

            start = offset+3
            pre = self.prev

            # Does this jump to right after another conditional jump that is
            # not myself?  If so, it's part of a larger conditional.
            # rocky: if we have a conditional jump to the next instruction, then
            # possibly I am "skipping over" a "pass" or null statement.

            if self.version < 2.7:
                op_testset = set([self.opc.POP_TOP,
                                   self.opc.JUMP_IF_TRUE, self.opc.JUMP_IF_FALSE])
            else:
                op_testset = self.pop_jump_if_or_pop | self.pop_jump_if

            if ( code[pre[target]] in op_testset
                 and (target > offset) ):
                self.fixed_jumps[offset] = pre[target]
                self.structs.append({'type':  'and/or',
                                       'start': start,
                                       'end':   pre[target]})
                return

            # The op offset just before the target jump offset is important
            # in making a determination of what we have. Save that.
            pre_rtarget = pre[rtarget]

            # Is it an "and" inside an "if" or "while" block
            if op == self.opc.PJIF:

                # Search for other POP_JUMP_IF_FALSE targetting the same op,
                # in current statement, starting from current offset, and filter
                # everything inside inner 'or' jumps and midline ifs
                match = self.rem_or(start, self.next_stmt[offset], self.opc.PJIF, target)

                # If we still have any offsets in set, start working on it
                if match:
                    if code[pre_rtarget] in self.jump_forward \
                            and pre_rtarget not in self.stmts \
                            and self.restrict_to_parent(self.get_target(pre_rtarget), parent) == rtarget:
                        if code[pre[pre_rtarget]] == self.opc.JUMP_ABSOLUTE \
                                and self.remove_mid_line_ifs([offset]) \
                                and target == self.get_target(pre[pre_rtarget]) \
                                and (pre[pre_rtarget] not in self.stmts or self.get_target(pre[pre_rtarget]) > pre[pre_rtarget])\
                                and 1 == len(self.remove_mid_line_ifs(self.rem_or(start, pre[pre_rtarget], self.pop_jump_if, target))):
                            pass
                        elif code[pre[pre_rtarget]] == self.opc.RETURN_VALUE \
                                and self.remove_mid_line_ifs([offset]) \
                                and 1 == (len(set(self.remove_mid_line_ifs(self.rem_or(start,
                                                                                       pre[pre_rtarget],
                                                                                       self.pop_jump_if, target)))
                                              | set(self.remove_mid_line_ifs(self.rem_or(start, pre[pre_rtarget],
                                                            (self.opc.PJIF, self.opc.PJIT, self.opc.JUMP_ABSOLUTE), pre_rtarget, True))))):
                            pass
                        else:
                            fix = None
                            jump_ifs = self.all_instr(start, self.next_stmt[offset], self.opc.PJIF)
                            last_jump_good = True
                            for j in jump_ifs:
                                if target == self.get_target(j):
                                    if self.lines[j].next == j+3 and last_jump_good:
                                        fix = j
                                        break
                                else:
                                    last_jump_good = False
                            self.fixed_jumps[offset] = fix or match[-1]
                            return
                    else:
                        if (self.version < 2.7
                            and parent['type'] in ('root', 'for-loop', 'if-then',
                                                   'else', 'try')):
                            self.fixed_jumps[offset] = rtarget
                        else:
                            # note test for < 2.7 might be superflous although informative
                            # for 2.7 a different branch is taken and the below code is handled
                            # under: elif op in self.pop_jump_if_or_pop
                            # below
                            self.fixed_jumps[offset] = match[-1]
                        return
            else: # op != self.opc.PJIT
                if self.version < 2.7 and code[offset+3] == self.opc.POP_TOP:
                    assert_offset = offset + 4
                else:
                    assert_offset = offset + 3
                if (assert_offset) in self.load_asserts:
                    if code[pre_rtarget] == self.opc.RAISE_VARARGS:
                        return
                    self.load_asserts.remove(assert_offset)

                next = self.next_stmt[offset]
                if pre[next] == offset:
                    pass
                elif code[next] in self.jump_forward and target == self.get_target(next):
                    if code[pre[next]] == self.opc.PJIF:
                        if code[next] == self.opc.JUMP_FORWARD or target != rtarget or code[pre[pre_rtarget]] not in (self.opc.JUMP_ABSOLUTE, self.opc.RETURN_VALUE):
                            self.fixed_jumps[offset] = pre[next]
                            return
                elif code[next] == self.opc.JUMP_ABSOLUTE and code[target] in self.jump_forward:
                    next_target = self.get_target(next)
                    if self.get_target(target) == next_target:
                        self.fixed_jumps[offset] = pre[next]
                        return
                    elif code[next_target] in self.jump_forward and self.get_target(next_target) == self.get_target(target):
                        self.fixed_jumps[offset] = pre[next]
                        return

            # don't add a struct for a while test, it's already taken care of
            if offset in self.ignore_if:
                return

            if self.version == 2.7:
                if code[pre_rtarget] == self.opc.JUMP_ABSOLUTE and pre_rtarget in self.stmts \
                        and pre_rtarget != offset and pre[pre_rtarget] != offset:
                    if code[rtarget] == self.opc.JUMP_ABSOLUTE and code[rtarget+3] == self.opc.POP_BLOCK:
                        if code[pre[pre_rtarget]] != self.opc.JUMP_ABSOLUTE:
                            pass
                        elif self.get_target(pre[pre_rtarget]) != target:
                            pass
                        else:
                            rtarget = pre_rtarget
                    else:
                        rtarget = pre_rtarget

            # Does the "jump if" jump beyond a jump op?
            # That is, we have something like:
            #  POP_JUMP_IF_FALSE HERE
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
            code_pre_rtarget = code[pre_rtarget]

            if code_pre_rtarget in self.jump_forward:
                if_end = self.get_target(pre_rtarget)

                # Is this a loop and not an "if" statment?
                if (if_end < pre_rtarget) and (pre[if_end] in self.setup_loop_targets):

                    if (if_end > start):
                        return
                    else:
                        # We still have the case in 2.7 that the next instruction
                        # is a jump to a SETUP_LOOP target.
                        next_offset = target + self.op_size(self.code[target])
                        next_op = self.code[next_offset]
                        if self.opc.opname[next_op] == 'JUMP_FORWARD':
                            jump_target = self.get_target(next_offset, next_op)
                            if jump_target in self.setup_loops:
                                self.structs.append({'type':  'while-loop',
                                       'start': jump_if_offset,
                                       'end':   jump_target})
                                self.fixed_jumps[jump_if_offset] = jump_target
                                return

                end = self.restrict_to_parent(if_end, parent)

                if_then_maybe = None

                if 2.2 <= self.version <= 2.6:
                    # Take the JUMP_IF target. In an "if/then", it will be
                    # a POP_TOP instruction and the instruction before it
                    # will be a JUMP_FORWARD to just after the POP_TOP.
                    # For example:
                    # Good:
                    # 3  JUMP_IF_FALSE        33  'to 39'
                    # ..
                    # 36  JUMP_FORWARD          1  'to 40'
                    # 39  POP_TOP
                    # 40 ...
                    # example:

                    # BAD (is an "and"):
                    # 28  JUMP_IF_FALSE         4  'to 35'
                    # ...
                    # 32  JUMP_ABSOLUTE        40  'to 40' # should be 36 or there should
                    #                                      # be a COME_FROM at the pop top
                    #                                      # before 40 to 35
                    # 35  POP_TOP
                    # 36 ...
                    # 39  POP_TOP
                    # 39_0  COME_FROM 3
                    # 40 ...

                    if self.opc.opname[code[jump_if_offset]].startswith('JUMP_IF'):
                        jump_if_target = code[jump_if_offset+1]
                        if self.opc.opname[code[jump_if_target + jump_if_offset + 3]] == 'POP_TOP':
                            jump_inst = jump_if_target + jump_if_offset
                            jump_offset = code[jump_inst+1]
                            jump_op = self.opc.opname[code[jump_inst]]
                            if (jump_op == 'JUMP_FORWARD' and jump_offset == 1):
                                self.structs.append({'type':  'if-then',
                                                     'start': start-3,
                                                     'end':   pre_rtarget})

                                self.thens[start] = end
                            elif jump_op == 'JUMP_ABSOLUTE':
                                if_then_maybe = {'type':  'if-then',
                                                 'start': start-3,
                                                 'end':   pre_rtarget}

                elif self.version == 2.7:
                    self.structs.append({'type':  'if-then',
                                         'start': start-3,
                                         'end':   pre_rtarget})

                self.not_continue.add(pre_rtarget)

                if rtarget < end:
                    # We have an "else" block  of some kind.
                    # Is it associated with "if_then_maybe" seen above?
                    # These will be linked in this funny way:

                    # 198  JUMP_IF_FALSE        18  'to 219'
                    # 201  POP_TOP
                    # ...
                    # 216  JUMP_ABSOLUTE       256  'to 256'
                    # 219  POP_TOP
                    # ...
                    # 252  JUMP_FORWARD          1  'to 256'
                    # 255  POP_TOP
                    # 256
                    if if_then_maybe and jump_op == 'JUMP_ABSOLUTE':
                        jump_target = self.get_target(jump_inst, code[jump_inst])
                        if self.opc.opname[code[end]] == 'JUMP_FORWARD':
                            end_target = self.get_target(end, code[end])
                            if jump_target == end_target:
                                self.structs.append(if_then_maybe)
                                self.thens[start] = end

                    self.structs.append({'type':  'else',
                                       'start': rtarget,
                                       'end':   end})
            elif code_pre_rtarget == self.opc.RETURN_VALUE:
                if self.version == 2.7 or pre_rtarget not in self.ignore_if:
                    self.structs.append({'type':  'if-then',
                                           'start': start,
                                           'end':   rtarget})
                    self.thens[start] = rtarget
                    if self.version == 2.7 or code[pre_rtarget+1] != self.opc.JUMP_FORWARD:
                        self.return_end_ifs.add(pre_rtarget)

        elif op in self.pop_jump_if_or_pop:
            target = self.get_target(offset, op)
            self.fixed_jumps[offset] = self.restrict_to_parent(target, parent)

    def find_jump_targets(self, debug):
        """
        Detect all offsets in a byte code which are jump targets
        where we might insert a pseudo "COME_FROM" instruction.
        "COME_FROM" instructions are used in detecting overall
        control flow. The more detailed information about the
        control flow is captured in self.structs.
        Since this stuff is tricky, consult self.structs when
        something goes amiss.

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
        self.ignore_if = set()
        self.build_statement_indices()

        # Containers filled by detect_control_flow()
        self.not_continue = set()
        self.return_end_ifs = set()
        self.setup_loop_targets = {}  # target given setup_loop offset
        self.setup_loops = {}  # setup_loop offset given target
        self.thens = {} # JUMP_IF's that separate the 'then' part of an 'if'

        targets = {}
        for offset in self.op_range(0, n):
            op = code[offset]

            # Determine structures and fix jumps in Python versions
            # since 2.3
            self.detect_control_flow(offset, op)

            if op_has_argument(op, self.opc):
                label = self.fixed_jumps.get(offset)
                oparg = self.get_argument(offset)

                if label is None:
                    if op in self.opc.hasjrel and self.opc.opname[op] != 'FOR_ITER':
                        # if (op in self.opc.hasjrel and
                        #     (self.version < 2.0 or op != self.opc.FOR_ITER)):
                        label = offset + 3 + oparg
                    elif self.version == 2.7 and op in self.opc.hasjabs:
                        if op in (self.opc.JUMP_IF_FALSE_OR_POP,
                                  self.opc.JUMP_IF_TRUE_OR_POP):
                            if (oparg > offset):
                                label = oparg
                                pass
                            pass

                # FIXME: All the < 2.7 conditions are is horrible. We need a better way.
                if label is not None and label != -1:
                    # In Python < 2.7, the POP_TOP in:
                    #   RETURN_VALUE, POP_TOP
                    # does now start a new statement
                    # Otherwise, we have want to add a "COME_FROM"
                    if not (self.version < 2.7 and
                            code[label] == self.opc.POP_TOP and
                            code[self.prev[label]] == self.opc.RETURN_VALUE):
                        # In Python < 2.7, don't add a COME_FROM, for:
                        #     JUMP_FORWARD, END_FINALLY
                        # or:
                        #     JUMP_FORWARD, POP_TOP, END_FINALLY
                        if not (self.version < 2.7 and op == self.opc.JUMP_FORWARD
                                and ((code[offset+3] == self.opc.END_FINALLY)
                                     or (code[offset+3] == self.opc.POP_TOP
                                         and code[offset+4] == self.opc.END_FINALLY))):

                            # FIXME: rocky: I think we need something like this...
                            if offset not in set(self.ignore_if) or self.version == 2.7:
                                if label in self.setup_loops:
                                    source = self.setup_loops[label]
                                else:
                                    source = offset
                                targets[label] = targets.get(label, []) + [source]
                            pass

                        pass
                    pass
            elif op == self.opc.END_FINALLY and offset in self.fixed_jumps and self.version == 2.7:
                label = self.fixed_jumps[offset]
                targets[label] = targets.get(label, []) + [offset]
                pass
            pass

        # DEBUG:
        if debug in ('both', 'after'):
            print(targets)
            import pprint as pp
            pp.pprint(self.structs)

        return targets

    # FIXME: combine with scanner3.py code and put into scanner.py
    def rem_or(self, start, end, instr, target=None, include_beyond_target=False):
        """
        Find all <instr> in the block from start to end.
        <instr> is any python bytecode instruction or a list of opcodes
        If <instr> is an opcode with a target (like a jump), a target
        destination can be specified which must match precisely.

        Return a list with indexes to them or [] if none found.
        """

        assert(start>=0 and end<=len(self.code) and start <= end)

        try:    None in instr
        except: instr = [instr]

        instr_offsets = []
        for i in self.op_range(start, end):
            op = self.code[i]
            if op in instr:
                if target is None:
                    instr_offsets.append(i)
                else:
                    t = self.get_target(i, op)
                    if include_beyond_target and t >= target:
                        instr_offsets.append(i)
                    elif t == target:
                        instr_offsets.append(i)

        pjits = self.all_instr(start, end, self.opc.PJIT)
        filtered = []
        for pjit in pjits:
            tgt = self.get_target(pjit)-3
            for i in instr_offsets:
                if i <= pjit or i >= tgt:
                    filtered.append(i)
            instr_offsets = filtered
            filtered = []
        return instr_offsets
