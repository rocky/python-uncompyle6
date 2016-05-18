#  Copyright (c) 2015, 2016 by Rocky Bernstein
#  Copyright (c) 2005 by Dan Pascu <dan@windowmaker.org>
#  Copyright (c) 2000-2002 by hartmut Goebel <h.goebel@crazy-compilers.com>
#  Copyright (c) 1999 John Aycock
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

import dis
import uncompyle6.scanners.dis3 as dis3

from collections import namedtuple
from array import array

from uncompyle6.code import iscode
from uncompyle6.scanner import Token
from uncompyle6 import PYTHON3


# Get all the opcodes into globals
import uncompyle6.opcodes.opcode_33 as op3

globals().update(op3.opmap)

POP_JUMP_TF = (POP_JUMP_IF_TRUE, POP_JUMP_IF_FALSE)

import uncompyle6.scanner as scan

class Scanner3(scan.Scanner):

    def __init__(self, version):
        if PYTHON3:
            super().__init__(version)
        else:
            super(Scanner3, self).__init__(version)

    def disassemble3(self, co, classname=None, code_objects={}):
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

        # import dis; dis.disassemble(co) # DEBUG

        # Container for tokens
        tokens = []

        self.code = array('B', co.co_code)
        self.build_lines_data(co)
        self.build_prev_op()

        bytecode = dis3.Bytecode(co, self.opname)

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
            elif opname == 'MAKE_FUNCTION':
                argc = inst.argval
                attr = ((argc & 0xFF), (argc >> 8) & 0xFF, (argc >> 16) & 0x7FFF)
                pos_args, name_pair_args, annotate_args = attr
                if name_pair_args > 0:
                    opname = 'MAKE_FUNCTION_N%d' % name_pair_args
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
            elif opname in ('BUILD_LIST', 'BUILD_TUPLE', 'BUILD_SET', 'BUILD_SLICE',
                            'BUILD_MAP', 'UNPACK_SEQUENCE', 'MAKE_CLOSURE',
                            'RAISE_VARARGS'
                            ):
                pos_args = inst.argval
                opname = '%s_%d' % (opname, pos_args)
            elif opname == 'JUMP_ABSOLUTE':
                pattr = inst.argval
                target = self.get_target(inst.offset)
                if target < inst.offset:
                    next_opname = self.opname[self.code[inst.offset+3]]
                    if (inst.offset in self.stmts and
                        next_opname not in ('END_FINALLY', 'POP_BLOCK')
                        and inst.offset not in self.not_continue):
                        opname = 'CONTINUE'
                    else:
                        opname = 'JUMP_BACK'

            elif inst.offset in self.load_asserts:
                opname = 'LOAD_ASSERT'

            tokens.append(
                Token(
                    type_ = opname,
                    attr = inst.argval,
                    pattr = pattr,
                    offset = inst.offset,
                    linestart = inst.starts_line,
                    )
                )
            pass
        return tokens, {}

    def disassemble3_native(self, co, classname=None, code_objects={}):
        """
        Like disassemble3 but doesn't try to adjust any opcodes.
        """
        # Container for tokens
        tokens = []

        self.code = array('B', co.co_code)

        bytecode = dis3.Bytecode(co, self.opname)

        for inst in bytecode:
            pattr =  inst.argrepr
            opname = inst.opname
            tokens.append(
                Token(
                    type_ = opname,
                    attr = inst.argval,
                    pattr = pattr,
                    offset = inst.offset,
                    linestart = inst.starts_line,
                    )
                )
            pass
        return tokens, {}

    def disassemble_generic(self, co, classname=None, code_objects={}):
        """
        Convert code object <co> into a sequence of tokens.

        The below is based on (an older version?) of Python dis.disassemble_bytes().
        """

        # dis.disassemble(co) # DEBUG
        # Container for tokens
        tokens = []
        customize = {}
        self.code = code = array('B', co.co_code)
        codelen = len(code)
        self.build_lines_data(co)
        self.build_prev_op()
        self.code_objects = code_objects

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
            pass

        # Scan for assertions. Later we will
        # turn 'LOAD_GLOBAL' to 'LOAD_ASSERT' for those
        # assertions
        self.load_asserts = set()
        for i in self.op_range(0, codelen):
            if (self.code[i] == POP_JUMP_IF_TRUE and
                self.code[i+3] == LOAD_GLOBAL):
                if names[self.get_argument(i+3)] == 'AssertionError':
                    self.load_asserts.add(i+3)

        # Get jump targets
        # Format: {target offset: [jump offsets]}
        jump_targets = self.find_jump_targets()

        # contains (code, [addrRefToCode])
        last_stmt = self.next_stmt[0]
        i = self.next_stmt[last_stmt]
        replace = {}

        imports = self.all_instr(0, codelen, (IMPORT_NAME, IMPORT_FROM, IMPORT_STAR))
        if len(imports) > 1:
            last_import = imports[0]
            for i in imports[1:]:
                if self.lines[last_import].next > i:
                    if self.code[last_import] == IMPORT_NAME == self.code[i]:
                        replace[i] = 'IMPORT_NAME_CONT'
                last_import = i

        # Initialize extended arg at 0. When extended arg op is encountered,
        # variable preserved for next cycle and added as arg for next op
        extended_arg = 0

        for offset in self.op_range(0, codelen):
            # Add jump target tokens
            if offset in jump_targets:
                jump_idx = 0
                for jump_offset in jump_targets[offset]:
                    tokens.append(Token('COME_FROM', None, repr(jump_offset),
                                        offset='%s_%s' % (offset, jump_idx)))
                    jump_idx += 1
                    pass
                pass

            op = code[offset]
            op_name = self.opname[op]

            oparg = None; pattr = None

            if op >= op3.HAVE_ARGUMENT:
                oparg = self.get_argument(offset) + extended_arg
                extended_arg = 0
                if op == op3.EXTENDED_ARG:
                    extended_arg = oparg * scan.L65536
                    continue
                if op in op3.hasconst:
                    const = co.co_consts[oparg]
                    if not PYTHON3 and isinstance(const, str):
                        if const in code_objects:
                            const = code_objects[const]
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
                        elif const.co_name == '<listcomp>':
                            op_name = 'LOAD_LISTCOMP'
                        # verify() uses 'pattr' for comparison, since 'attr'
                        # now holds Code(const) and thus can not be used
                        # for comparison (todo: think about changing this)
                        # pattr = 'code_object @ 0x%x %s->%s' %\
                        # (id(const), const.co_filename, const.co_name)
                        pattr = '<code_object ' + const.co_name + '>'
                    else:
                        pattr = const
                elif op in op3.hasname:
                    pattr = names[oparg]
                elif op in op3.hasjrel:
                    pattr = repr(offset + 3 + oparg)
                elif op in op3.hasjabs:
                    pattr = repr(oparg)
                elif op in op3.haslocal:
                    pattr = varnames[oparg]
                elif op in op3.hascompare:
                    pattr = op3.cmp_op[oparg]
                elif op in op3.hasfree:
                    pattr = free[oparg]

            if op_name == 'MAKE_FUNCTION':
                argc = oparg
                attr = ((argc & 0xFF), (argc >> 8) & 0xFF, (argc >> 16) & 0x7FFF)
                pos_args, name_pair_args, annotate_args = attr
                if name_pair_args > 0:
                    op_name = 'MAKE_FUNCTION_N%d' % name_pair_args
                    pass
                if annotate_args > 0:
                    op_name = '%s_A_%d' % [op_name, annotate_args]
                    pass
                op_name = '%s_%d' % (op_name, pos_args)
                pattr = ("%d positional, %d keyword pair, %d annotated" %
                             (pos_args, name_pair_args, annotate_args))
                tokens.append(
                    Token(
                        type_ = op_name,
                        attr = (pos_args, name_pair_args, annotate_args),
                        pattr = pattr,
                        offset = offset,
                        linestart = linestart)
                    )
                continue
            elif op_name in ('BUILD_LIST', 'BUILD_TUPLE', 'BUILD_SET', 'BUILD_SLICE',
                            'UNPACK_SEQUENCE',
                            'MAKE_FUNCTION', 'CALL_FUNCTION', 'MAKE_CLOSURE',
                            'CALL_FUNCTION_VAR', 'CALL_FUNCTION_KW',
                            'CALL_FUNCTION_VAR_KW', 'RAISE_VARARGS'
                            ):
                # CALL_FUNCTION OP renaming is done as a custom rule in parse3
                if op_name not in ('CALL_FUNCTION', 'CALL_FUNCTION_VAR',
                                   'CALL_FUNCTION_VAR_KW', 'CALL_FUNCTION_KW',
                                   ):
                    op_name = '%s_%d' % (op_name, oparg)
                    if op_name != 'BUILD_SLICE':
                        customize[op_name] = oparg
            elif op_name == 'JUMP_ABSOLUTE':
                target = self.get_target(offset)
                if target < offset:
                    if (offset in self.stmts
                        and self.code[offset+3] not in (END_FINALLY, POP_BLOCK)
                        and offset not in self.not_continue):
                        op_name = 'CONTINUE'
                    else:
                        op_name = 'JUMP_BACK'
                        pass
                    pass
                pass
            elif op_name == 'JUMP_FORWARD':
                # Python 3.5 will optimize out a JUMP_FORWARD to the
                # next instruction while Python 3.2 won't. Smplify
                # grammar rules working with both 3.2 and 3.5,
                # by optimizing the way Python 3.5 does it.
                #
                # We may however want to consider whether we do
                # this in 3.5 or not.
                if oparg == 0 and self.version >= 3.5:
                    tokens.append(Token('NOP', oparg, pattr, offset, linestart))
                    continue
            elif op_name == 'LOAD_GLOBAL':
                if offset in self.load_asserts:
                    op_name = 'LOAD_ASSERT'

            if offset in self.linestarts:
                linestart = self.linestarts[offset]
            else:
                linestart = None

            if offset not in replace:
                tokens.append(Token(op_name, oparg, pattr, offset, linestart))
            else:
                tokens.append(Token(replace[offset], oparg, pattr, offset, linestart))
            pass

        # debug:
        # for t in tokens:
        #   print(t)
        return tokens, customize

    def build_lines_data(self, code_obj):
        """
        Generate various line-related helper data.
        """
        # Offset: lineno pairs, only for offsets which start line.
        # Locally we use list for more convenient iteration using indices
        linestarts = list(dis.findlinestarts(code_obj))
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
        self.prev_op = [0]
        for offset in self.op_range(0, codelen):
            op = code[offset]
            for _ in range(self.op_size(op)):
                self.prev_op.append(offset)

    def op_size(self, op):
        """
        Return size of operator with its arguments
        for given opcode <op>.
        """
        if op < dis.HAVE_ARGUMENT:
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
                    if op in op3.hasjrel and op != FOR_ITER:
                        label = offset + self.op_size(op) + oparg
                    elif op in op3.hasjabs:
                        if op in (JUMP_IF_FALSE_OR_POP, JUMP_IF_TRUE_OR_POP):
                            if oparg > offset:
                                label = oparg

                if label is not None and label != -1:
                    targets[label] = targets.get(label, []) + [offset]
            elif op == END_FINALLY and offset in self.fixed_jumps:
                label = self.fixed_jumps[offset]
                targets[label] = targets.get(label, []) + [offset]
        return targets

    def build_statement_indices(self):
        code = self.code
        start = 0
        end = codelen = len(code)

        statement_opcodes = set([
            SETUP_LOOP, BREAK_LOOP, CONTINUE_LOOP,
            SETUP_FINALLY, END_FINALLY, SETUP_EXCEPT, SETUP_WITH,
            POP_BLOCK, STORE_FAST, DELETE_FAST, STORE_DEREF,
            STORE_GLOBAL, DELETE_GLOBAL, STORE_NAME, DELETE_NAME,
            STORE_ATTR, DELETE_ATTR, STORE_SUBSCR, DELETE_SUBSCR,
            RETURN_VALUE, RAISE_VARARGS, POP_TOP, PRINT_EXPR,
            JUMP_ABSOLUTE
        ])

        statement_opcode_sequences = [(POP_JUMP_IF_FALSE, JUMP_FORWARD), (POP_JUMP_IF_FALSE, JUMP_ABSOLUTE),
                                      (POP_JUMP_IF_TRUE, JUMP_FORWARD), (POP_JUMP_IF_TRUE, JUMP_ABSOLUTE)]

        designator_ops = set([
            STORE_FAST, STORE_NAME, STORE_GLOBAL, STORE_DEREF, STORE_ATTR,
            STORE_SUBSCR, UNPACK_SEQUENCE, JUMP_ABSOLUTE
        ])

        # Compose preliminary list of indices with statements,
        # using plain statement opcodes
        prelim = self.all_instr(start, end, statement_opcodes)

        # Initialize final container with statements with
        # preliminnary data
        stmts = self.stmts = set(prelim)

        # Same for opcode sequences
        pass_stmts = set()
        for sequence in statement_opcode_sequences:
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
            if code[stmt_offset] == JUMP_ABSOLUTE and stmt_offset not in pass_stmts:
                # If absolute jump occurs in forward direction or it takes off from the
                # same line as previous statement, this is not a statement
                target = self.get_target(stmt_offset)
                if target > stmt_offset or self.lines[last_stmt_offset].l_no == self.lines[stmt_offset].l_no:
                    stmts.remove(stmt_offset)
                    continue
                # Rewing ops till we encounter non-JA one
                j = self.prev_op[stmt_offset]
                while code[j] == JUMP_ABSOLUTE:
                    j = self.prev_op[j]
                # If we got here, then it's list comprehension which
                # is not a statement too
                if code[j] == LIST_APPEND:
                    stmts.remove(stmt_offset)
                    continue
            # Exclude ROT_TWO + POP_TOP
            elif code[stmt_offset] == POP_TOP and code[self.prev_op[stmt_offset]] == ROT_TWO:
                stmts.remove(stmt_offset)
                continue
            # Exclude FOR_ITER + designators
            elif code[stmt_offset] in designator_ops:
                j = self.prev_op[stmt_offset]
                while code[j] in designator_ops:
                    j = self.prev_op[j]
                if code[j] == FOR_ITER:
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
            curent_start = struct['start']
            curent_end   = struct['end']
            if (curent_start <= offset < curent_end) and (curent_start >= start and curent_end <= end):
                start = curent_start
                end = curent_end
                parent = struct

        if op == SETUP_LOOP:
            start = offset+3
            target = self.get_target(offset)
            end    = self.restrict_to_parent(target, parent)

            if target != end:
                self.fixed_jumps[offset] = end
            (line_no, next_line_byte) = self.lines[offset]
            jump_back = self.last_instr(start, end, JUMP_ABSOLUTE,
                                          next_line_byte, False)

            if jump_back and jump_back != self.prev_op[end] and code[jump_back+3] in (JUMP_ABSOLUTE, JUMP_FORWARD):
                if code[self.prev_op[end]] == RETURN_VALUE or \
                    (code[self.prev_op[end]] == POP_BLOCK and code[self.prev_op[self.prev_op[end]]] == RETURN_VALUE):
                    jump_back = None
            if not jump_back: # loop suite ends in return. wtf right?
                jump_back = self.last_instr(start, end, RETURN_VALUE) + 1
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
                    jump_back = self.last_instr(start, end, JUMP_ABSOLUTE, start, False)
                if end > jump_back+4 and code[end] in (JUMP_FORWARD, JUMP_ABSOLUTE):
                    if code[jump_back+4] in (JUMP_ABSOLUTE, JUMP_FORWARD):
                        if self.get_target(jump_back+4) == self.get_target(end):
                            self.fixed_jumps[offset] = jump_back+4
                            end = jump_back+4
                elif target < offset:
                    self.fixed_jumps[offset] = jump_back+4
                    end = jump_back+4
                target = self.get_target(jump_back)

                if code[target] in (FOR_ITER, GET_ITER):
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

            # Does this jump to right after another cond jump that is
            # not myself?  If so, it's part of a larger conditional.
            # rocky: if we have a conditional jump to the next instruction, then
            # possibly I am "skipping over" a "pass" or null statement.
            if ((code[prev_op[target]] in
                    (JUMP_IF_FALSE_OR_POP, JUMP_IF_TRUE_OR_POP,
                     POP_JUMP_IF_FALSE, POP_JUMP_IF_TRUE)) and
                (target > offset) and prev_op[target] != offset):
                self.fixed_jumps[offset] = prev_op[target]
                self.structs.append({'type': 'and/or',
                                     'start': start,
                                     'end': prev_op[target]})
                return

            # Is it an and inside if block
            if op == POP_JUMP_IF_FALSE:
                # Search for other POP_JUMP_IF_FALSE targetting the same op,
                # in current statement, starting from current offset, and filter
                # everything inside inner 'or' jumps and midline ifs
                match = self.rem_or(start, self.next_stmt[offset], POP_JUMP_IF_FALSE, target)
                match = self.remove_mid_line_ifs(match)
                # If we still have any offsets in set, start working on it
                if match:
                    if (code[prev_op[rtarget]] in (JUMP_FORWARD, JUMP_ABSOLUTE) and prev_op[rtarget] not in self.stmts and
                        self.restrict_to_parent(self.get_target(prev_op[rtarget]), parent) == rtarget):
                        if (code[prev_op[prev_op[rtarget]]] == JUMP_ABSOLUTE and self.remove_mid_line_ifs([offset]) and
                            target == self.get_target(prev_op[prev_op[rtarget]]) and
                            (prev_op[prev_op[rtarget]] not in self.stmts or self.get_target(prev_op[prev_op[rtarget]]) > prev_op[prev_op[rtarget]]) and
                            1 == len(self.remove_mid_line_ifs(self.rem_or(start, prev_op[prev_op[rtarget]], POP_JUMP_TF, target)))):
                            pass
                        elif (code[prev_op[prev_op[rtarget]]] == RETURN_VALUE and self.remove_mid_line_ifs([offset]) and
                              1 == (len(set(self.remove_mid_line_ifs(self.rem_or(start, prev_op[prev_op[rtarget]],
                                                                                 POP_JUMP_TF, target))) |
                                    set(self.remove_mid_line_ifs(self.rem_or(start, prev_op[prev_op[rtarget]],
                                                                             (POP_JUMP_IF_FALSE, POP_JUMP_IF_TRUE, JUMP_ABSOLUTE),
                                                                             prev_op[rtarget], True)))))):
                            pass
                        else:
                            fix = None
                            jump_ifs = self.all_instr(start, self.next_stmt[offset], POP_JUMP_IF_FALSE)
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
                        self.fixed_jumps[offset] = match[-1]
                        return
            # op == POP_JUMP_IF_TRUE
            else:
                next = self.next_stmt[offset]
                if prev_op[next] == offset:
                    pass
                elif code[next] in (JUMP_FORWARD, JUMP_ABSOLUTE) and target == self.get_target(next):
                    if code[prev_op[next]] == POP_JUMP_IF_FALSE:
                        if code[next] == JUMP_FORWARD or target != rtarget or code[prev_op[prev_op[rtarget]]] not in (JUMP_ABSOLUTE, RETURN_VALUE):
                            self.fixed_jumps[offset] = prev_op[next]
                            return
                elif (code[next] == JUMP_ABSOLUTE and code[target] in (JUMP_ABSOLUTE, JUMP_FORWARD) and
                      self.get_target(target) == self.get_target(next)):
                    self.fixed_jumps[offset] = prev_op[next]
                    return

            # Don't add a struct for a while test, it's already taken care of
            if offset in self.ignore_if:
                return

            if (code[prev_op[rtarget]] == JUMP_ABSOLUTE and prev_op[rtarget] in self.stmts and
                prev_op[rtarget] != offset and prev_op[prev_op[rtarget]] != offset and
                not (code[rtarget] == JUMP_ABSOLUTE and code[rtarget+3] == POP_BLOCK and code[prev_op[prev_op[rtarget]]] != JUMP_ABSOLUTE)):
                rtarget = prev_op[rtarget]

            # Does the if jump just beyond a jump op, then this is probably an if statement
            if code[prev_op[rtarget]] in (JUMP_ABSOLUTE, JUMP_FORWARD):
                if_end = self.get_target(prev_op[rtarget])

                # Is this a loop not an if?
                if (if_end < prev_op[rtarget]) and (code[prev_op[if_end]] == SETUP_LOOP):
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
            elif code[prev_op[rtarget]] == RETURN_VALUE:
                self.structs.append({'type': 'if-then',
                                     'start': start,
                                     'end': rtarget})
                self.return_end_ifs.add(prev_op[rtarget])

        elif op in (JUMP_IF_FALSE_OR_POP, JUMP_IF_TRUE_OR_POP):
            target = self.get_target(offset)
            if target > offset:
                unop_target = self.last_instr(offset, target, JUMP_FORWARD, target)
                if unop_target and code[unop_target+3] != ROT_TWO:
                    self.fixed_jumps[offset] = unop_target
                else:
                    self.fixed_jumps[offset] = self.restrict_to_parent(target, parent)

    def next_except_jump(self, start):
        """
        Return the next jump that was generated by an except SomeException:
        construct in a try...except...else clause or None if not found.
        """

        if self.code[start] == DUP_TOP:
            except_match = self.first_instr(start, len(self.code), POP_JUMP_IF_FALSE)
            if except_match:
                jmp = self.prev_op[self.get_target(except_match)]
                self.ignore_if.add(except_match)
                self.not_continue.add(jmp)
                return jmp

        count_END_FINALLY = 0
        count_SETUP_ = 0
        for i in self.op_range(start, len(self.code)):
            op = self.code[i]
            if op == END_FINALLY:
                if count_END_FINALLY == count_SETUP_:
                    assert self.code[self.prev_op[i]] in (JUMP_ABSOLUTE, JUMP_FORWARD, RETURN_VALUE)
                    self.not_continue.add(self.prev_op[i])
                    return self.prev_op[i]
                count_END_FINALLY += 1
            elif op in (SETUP_EXCEPT, SETUP_WITH, SETUP_FINALLY):
                count_SETUP_ += 1

    def rem_or(self, start, end, instr, target=None, include_beyond_target=False):
        """
        Find offsets of all requested <instr> between <start> and <end>,
        optionally <target>ing specified offset, and return list found
        <instr> offsets which are not within any POP_JUMP_IF_TRUE jumps.
        """
        # Find all offsets of requested instructions
        instr_offsets = self.all_instr(start, end, instr, target, include_beyond_target)
        # Get all POP_JUMP_IF_TRUE (or) offsets
        pjit_offsets = self.all_instr(start, end, POP_JUMP_IF_TRUE)
        filtered = []
        for pjit_offset in pjit_offsets:
            pjit_tgt = self.get_target(pjit_offset) - 3
            for instr_offset in instr_offsets:
                if instr_offset <= pjit_offset or instr_offset >= pjit_tgt:
                    filtered.append(instr_offset)
            instr_offsets = filtered
            filtered = []
        return instr_offsets

    def remove_mid_line_ifs(self, ifs):
        """
        Go through passed offsets, filtering ifs
        located somewhere mid-line.
        """
        filtered = []
        for if_ in ifs:
            # For each offset, if line number of current and next op
            # is the same
            if self.lines[if_].l_no == self.lines[if_+3].l_no:
                # Skip last op on line if it is some sort of POP_JUMP.
                if self.code[self.prev_op[self.lines[if_].next]] in POP_JUMP_TF:
                    continue
            filtered.append(if_)
        return filtered

if __name__ == "__main__":
    from uncompyle6 import PYTHON_VERSION
    if PYTHON_VERSION >= 3.2:
        import inspect
        co = inspect.currentframe().f_code
        from uncompyle6 import PYTHON_VERSION
        tokens, customize = Scanner3(PYTHON_VERSION).disassemble3(co)
        for t in tokens:
            print(t.format())
    else:
        print("Need to be Python 3.2 or greater to demo; I am %s." %
              PYTHON_VERSION)
    pass
