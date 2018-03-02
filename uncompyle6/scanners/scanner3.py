#  Copyright (c) 2015-2018 by Rocky Bernstein
#  Copyright (c) 2005 by Dan Pascu <dan@windowmaker.org>
#  Copyright (c) 2000-2002 by hartmut Goebel <h.goebel@crazy-compilers.com>
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
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

from uncompyle6 import PYTHON_VERSION

if PYTHON_VERSION < 2.6:
    from xdis.namedtuple24 import namedtuple
else:
    from collections import namedtuple

from array import array

from xdis.code import iscode
from xdis.bytecode import Bytecode, instruction_size, _get_const_info

from uncompyle6.scanner import Token, parse_fn_counts
import xdis

# Get all the opcodes into globals
import xdis.opcodes.opcode_33 as op3

from uncompyle6.scanner import Scanner

import sys
from uncompyle6 import PYTHON3
if PYTHON3:
    intern = sys.intern

globals().update(op3.opmap)

class Scanner3(Scanner):

    def __init__(self, version, show_asm=None, is_pypy=False):
        super(Scanner3, self).__init__(version, show_asm, is_pypy)

        # Create opcode classification sets
        # Note: super initilization above initializes self.opc

        # Ops that start SETUP_ ... We will COME_FROM with these names
        # Some blocks and END_ statements. And they can start
        # a new statement
        setup_ops = [self.opc.SETUP_LOOP, self.opc.SETUP_EXCEPT,
                      self.opc.SETUP_FINALLY]

        if self.version >= 3.2:
            setup_ops.append(self.opc.SETUP_WITH)
        self.setup_ops = frozenset(setup_ops)

        if self.version == 3.0:
            self.pop_jump_tf = frozenset([self.opc.JUMP_IF_FALSE, self.opc.JUMP_IF_TRUE])
        else:
            self.pop_jump_tf = frozenset([self.opc.PJIF, self.opc.PJIT])

        self.setup_ops_no_loop = frozenset(setup_ops) - frozenset([self.opc.SETUP_LOOP])

        # Opcodes that can start a statement.
        statement_opcodes = [
            self.opc.BREAK_LOOP,    self.opc.CONTINUE_LOOP,
            self.opc.POP_BLOCK,     self.opc.STORE_FAST,
            self.opc.DELETE_FAST,   self.opc.STORE_DEREF,

            self.opc.STORE_GLOBAL,  self.opc.DELETE_GLOBAL,
            self.opc.STORE_NAME,    self.opc.DELETE_NAME,

            self.opc.STORE_ATTR,    self.opc.DELETE_ATTR,
            self.opc.STORE_SUBSCR,  self.opc.POP_TOP,
            self.opc.DELETE_SUBSCR, self.opc.END_FINALLY,

            self.opc.RETURN_VALUE, self.opc.RAISE_VARARGS,
            self.opc.PRINT_EXPR,   self.opc.JUMP_ABSOLUTE
        ]

        self.statement_opcodes = frozenset(statement_opcodes) | self.setup_ops_no_loop

        # Opcodes that can start a designator non-terminal.
        # FIXME: JUMP_ABSOLUTE is weird. What's up with that?
        self.designator_ops = frozenset([
            self.opc.STORE_FAST,    self.opc.STORE_NAME, self.opc.STORE_GLOBAL,
            self.opc.STORE_DEREF,   self.opc.STORE_ATTR,
            self.opc.STORE_SUBSCR,  self.opc.UNPACK_SEQUENCE,
            self.opc.JUMP_ABSOLUTE, self.opc.UNPACK_EX
        ])

        if self.version > 3.0:
            self.jump_if_pop = frozenset([self.opc.JUMP_IF_FALSE_OR_POP,
                                          self.opc.JUMP_IF_TRUE_OR_POP])

            self.pop_jump_if_pop = frozenset([self.opc.JUMP_IF_FALSE_OR_POP,
                                              self.opc.JUMP_IF_TRUE_OR_POP,
                                              self.opc.POP_JUMP_IF_TRUE,
                                              self.opc.POP_JUMP_IF_FALSE])
            # Not really a set, but still clasification-like
            self.statement_opcode_sequences = [
                (self.opc.POP_JUMP_IF_FALSE, self.opc.JUMP_FORWARD),
                (self.opc.POP_JUMP_IF_FALSE, self.opc.JUMP_ABSOLUTE),
                (self.opc.POP_JUMP_IF_TRUE,  self.opc.JUMP_FORWARD),
                (self.opc.POP_JUMP_IF_TRUE,  self.opc.JUMP_ABSOLUTE)]

        else:
            self.jump_if_pop = frozenset([])
            self.pop_jump_if_pop = frozenset([])
            # Not really a set, but still clasification-like
            self.statement_opcode_sequences = [
                (self.opc.JUMP_FORWARD,),
                (self.opc.JUMP_ABSOLUTE,),
                (self.opc.JUMP_FORWARD,),
                (self.opc.JUMP_ABSOLUTE,)]

        # Opcodes that take a variable number of arguments
        # (expr's)
        varargs_ops = set([
             self.opc.BUILD_LIST,       self.opc.BUILD_TUPLE,
             self.opc.BUILD_SET,        self.opc.BUILD_SLICE,
             self.opc.BUILD_MAP,        self.opc.UNPACK_SEQUENCE,
             self.opc.RAISE_VARARGS])

        if is_pypy:
            varargs_ops.add(self.opc.CALL_METHOD)
        if self.version >= 3.6:
            varargs_ops.add(self.opc.BUILD_CONST_KEY_MAP)
            # Below is in bit order, "default = bit 0, closure = bit 3
            self.MAKE_FUNCTION_FLAGS = tuple("""
             default keyword-only annotation closure""".split())

        self.varargs_ops = frozenset(varargs_ops)
        # FIXME: remove the above in favor of:
        # self.varargs_ops = frozenset(self.opc.hasvargs)

    def remove_extended_args(self, instructions):
        """Go through instructions removing extended ARG.
        get_instruction_bytes previously adjusted the operand values
        to account for these"""
        new_instructions = []
        last_was_extarg = False
        n = len(instructions)
        for i, inst in enumerate(instructions):
            if (inst.opname == 'EXTENDED_ARG' and
                i+1 < n and instructions[i+1].opname != 'MAKE_FUNCTION'):
                last_was_extarg = True
                starts_line = inst.starts_line
                is_jump_target = inst.is_jump_target
                offset = inst.offset
                continue
            if last_was_extarg:

                # j = self.stmts.index(inst.offset)
                # self.lines[j] = offset

                new_inst= inst._replace(starts_line=starts_line,
                                        is_jump_target=is_jump_target,
                                        offset=offset)
                inst = new_inst
                if i < n:
                    new_prev = self.prev_op[instructions[i].offset]
                    j = instructions[i+1].offset
                    old_prev = self.prev_op[j]
                    while self.prev_op[j] == old_prev and j < n:
                        self.prev_op[j] = new_prev
                        j += 1

            last_was_extarg = False
            new_instructions.append(inst)
        return new_instructions

    def ingest(self, co, classname=None, code_objects={}, show_asm=None):
        """
        Pick out tokens from an uncompyle6 code object, and transform them,
        returning a list of uncompyle6 Token's.

        The transformations are made to assist the deparsing grammar.
        Specificially:
           -  various types of LOAD_CONST's are categorized in terms of what they load
           -  COME_FROM instructions are added to assist parsing control structures
           -  MAKE_FUNCTION and FUNCTION_CALLS append the number of positional arguments
           -  some EXTENDED_ARGS instructions are removed

        Also, when we encounter certain tokens, we add them to a set which will cause custom
        grammar rules. Specifically, variable arg tokens like MAKE_FUNCTION or BUILD_LIST
        cause specific rules for the specific number of arguments they take.
        """

        # FIXME: remove this when all subsidiary functions have been removed.
        # We should be able to get everything from the self.insts list.
        self.code = array('B', co.co_code)

        bytecode = Bytecode(co, self.opc)
        if not show_asm:
            show_asm = self.show_asm

        # show_asm = 'both'
        if show_asm in ('both', 'before'):
            for instr in bytecode.get_instructions(co):
                print(instr.disassemble())

        # list of tokens/instructions
        tokens = []

        # "customize" is in the process of going away here
        customize = {}

        if self.is_pypy:
            customize['PyPy'] = 0

        self.lines = self.build_lines_data(co)
        self.build_prev_op()

        # FIXME: put as its own method?
        # Scan for assertions. Later we will
        # turn 'LOAD_GLOBAL' to 'LOAD_ASSERT'.
        # 'LOAD_ASSERT' is used in assert statements.
        self.load_asserts = set()
        self.insts = self.remove_extended_args(list(bytecode))

        self.offset2inst_index = {}
        n = len(self.insts)
        for i, inst in enumerate(self.insts):

            self.offset2inst_index[inst.offset] = i

            # We need to detect the difference between:
            #   raise AssertionError
            #  and
            #   assert ...
            # If we have a JUMP_FORWARD after the
            # RAISE_VARARGS then we have a "raise" statement
            # else we have an "assert" statement.
            if inst.opname == 'POP_JUMP_IF_TRUE' and i+1 < n:
                next_inst = self.insts[i+1]
                if (next_inst.opname == 'LOAD_GLOBAL' and
                    next_inst.argval == 'AssertionError'):
                    if (i + 2 < n and self.insts[i+2].opname.startswith('RAISE_VARARGS')):
                        self.load_asserts.add(next_inst.offset)
                    pass
                pass

        # Get jump targets
        # Format: {target offset: [jump offsets]}
        jump_targets = self.find_jump_targets(show_asm)
        # print("XXX2", jump_targets)

        last_op_was_break = False

        for i, inst in enumerate(self.insts):

            argval = inst.argval
            op     = inst.opcode

            if inst.opname == 'EXTENDED_ARG':
                # FIXME: The EXTENDED_ARG is used to signal annotation
                # parameters
                if (i+1 < n and
                    self.insts[i+1].opcode != self.opc.MAKE_FUNCTION):
                    continue

            if inst.offset in jump_targets:
                jump_idx = 0
                # We want to process COME_FROMs to the same offset to be in *descending*
                # offset order so we have the larger range or biggest instruction interval
                # last. (I think they are sorted in increasing order, but for safety
                # we sort them). That way, specific COME_FROM tags will match up
                # properly. For example, a "loop" with an "if" nested in it should have the
                # "loop" tag last so the grammar rule matches that properly.
                for jump_offset in sorted(jump_targets[inst.offset], reverse=True):
                    come_from_name = 'COME_FROM'
                    opname = self.opname_for_offset(jump_offset)
                    if opname == 'EXTENDED_ARG':
                        j = xdis.next_offset(op, self.opc, jump_offset)
                        opname = self.opname_for_offset(j)

                    if opname.startswith('SETUP_'):
                        come_from_type = opname[len('SETUP_'):]
                        come_from_name = 'COME_FROM_%s' % come_from_type
                        pass
                    elif inst.offset in self.except_targets:
                        come_from_name = 'COME_FROM_EXCEPT_CLAUSE'
                    tokens.append(Token(come_from_name,
                                        jump_offset, repr(jump_offset),
                                        offset='%s_%s' % (inst.offset, jump_idx),
                                        has_arg = True, opc=self.opc))
                    jump_idx += 1
                    pass
                pass
            elif inst.offset in self.else_start:
                end_offset = self.else_start[inst.offset]
                tokens.append(Token('ELSE',
                                    None, repr(end_offset),
                                    offset='%s' % (inst.offset),
                                    has_arg = True, opc=self.opc))

                pass

            pattr  = inst.argrepr
            opname = inst.opname

            if op in self.opc.CONST_OPS:
                const = argval
                if iscode(const):
                    if const.co_name == '<lambda>':
                        assert opname == 'LOAD_CONST'
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
                    if isinstance(inst.arg, int) and inst.arg < len(co.co_consts):
                        argval, _ = _get_const_info(inst.arg, co.co_consts)
                    # Why don't we use _ above for "pattr" rather than "const"?
                    # This *is* a little hoaky, but we have to coordinate with
                    # other parts like n_LOAD_CONST in pysource.py for example.
                    pattr = const
                    pass
            elif opname in ('MAKE_FUNCTION', 'MAKE_CLOSURE'):
                if self.version >= 3.6:
                    # 3.6+ doesn't have MAKE_CLOSURE, so opname == 'MAKE_FUNCTION'
                    flags = argval
                    opname = 'MAKE_FUNCTION_%d' % (flags)
                    attr = []
                    for flag in self.MAKE_FUNCTION_FLAGS:
                        bit = flags & 1
                        attr.append(bit)
                        flags >>= 1
                    attr = attr[:4] # remove last value: attr[5] == False
                else:
                    pos_args, name_pair_args, annotate_args = parse_fn_counts(inst.argval)
                    pattr = ("%d positional, %d keyword pair, %d annotated" %
                                 (pos_args, name_pair_args, annotate_args))
                    if name_pair_args > 0:
                        opname = '%s_N%d' % (opname, name_pair_args)
                        pass
                    if annotate_args > 0:
                        opname = '%s_A_%d' % (opname, annotate_args)
                        pass
                    opname = '%s_%d' % (opname, pos_args)
                    attr = (pos_args, name_pair_args, annotate_args)
                tokens.append(
                    Token(
                        opname = opname,
                        attr = attr,
                        pattr = pattr,
                        offset = inst.offset,
                        linestart = inst.starts_line,
                        op = op,
                        has_arg = inst.has_arg,
                        opc = self.opc
                    )
                )
                continue
            elif op in self.varargs_ops:
                pos_args = argval
                if self.is_pypy and not pos_args and opname == 'BUILD_MAP':
                    opname = 'BUILD_MAP_n'
                else:
                    opname = '%s_%d' % (opname, pos_args)

            elif self.is_pypy and opname in ('CALL_METHOD', 'JUMP_IF_NOT_DEBUG'):
                # The value in the dict is in special cases in semantic actions, such
                # as CALL_FUNCTION. The value is not used in these cases, so we put
                # in arbitrary value 0.
                customize[opname] = 0
            elif opname == 'UNPACK_EX':
                # FIXME: try with scanner and parser by
                # changing argval
                before_args = argval & 0xFF
                after_args = (argval >> 8) & 0xff
                pattr = "%d before vararg, %d after" % (before_args, after_args)
                argval = (before_args, after_args)
                opname = '%s_%d+%d' % (opname, before_args, after_args)

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
                pattr = argval
                target = self.get_target(inst.offset)
                if target <= inst.offset:
                    next_opname = self.insts[i+1].opname

                    # 'Continue's include jumps to loops that are not
                    # and the end of a block which follow with POP_BLOCK and COME_FROM_LOOP.
                    # If the JUMP_ABSOLUTE is to a FOR_ITER and it is followed by another JUMP_FORWARD
                    # then we'll take it as a "continue".
                    is_continue = (self.insts[self.offset2inst_index[target]]
                                  .opname == 'FOR_ITER'
                                  and self.insts[i+1].opname == 'JUMP_FORWARD')

                    if (is_continue or
                        (inst.offset in self.stmts and
                        (self.version != 3.0 or (hasattr(inst, 'linestart'))) and
                        (next_opname not in ('END_FINALLY', 'POP_BLOCK',
                                            # Python 3.0 only uses POP_TOP
                                            'POP_TOP')))):
                        opname = 'CONTINUE'
                    else:
                        opname = 'JUMP_BACK'
                        # FIXME: this is a hack to catch stuff like:
                        #   if x: continue
                        # the "continue" is not on a new line.
                        # There are other situations where we don't catch
                        # CONTINUE as well.
                        if tokens[-1].kind == 'JUMP_BACK' and tokens[-1].attr <= argval:
                            if tokens[-2].kind == 'BREAK_LOOP':
                                del tokens[-1]
                            else:
                                # intern is used because we are changing the *previous* token
                                tokens[-1].kind = intern('CONTINUE')
                    if last_op_was_break and opname == 'CONTINUE':
                        last_op_was_break = False
                        continue

            # FIXME: go over for Python 3.6+. This is sometimes wrong
            elif op == self.opc.RETURN_VALUE:
                if inst.offset in self.return_end_ifs:
                    opname = 'RETURN_END_IF'

            elif inst.offset in self.load_asserts:
                opname = 'LOAD_ASSERT'

            last_op_was_break = opname == 'BREAK_LOOP'
            tokens.append(
                Token(
                    opname = opname,
                    attr = argval,
                    pattr = pattr,
                    offset = inst.offset,
                    linestart = inst.starts_line,
                    op = op,
                    has_arg = inst.has_arg,
                    opc = self.opc
                    )
                )
            pass

        if show_asm in ('both', 'after'):
            for t in tokens:
                print(t.format(line_prefix='L.'))
            print()
        return tokens, customize

    def build_lines_data(self, code_obj):
        """
        Generate various line-related helper data.
        """
        # Offset: lineno pairs, only for offsets which start line.
        # Locally we use list for more convenient iteration using indices
        linestarts = list(self.opc.findlinestarts(code_obj))
        self.linestarts = dict(linestarts)
        # Plain set with offsets of first ops on line
        self.linestart_offsets = set(a for (a, _) in linestarts)
        # 'List-map' which shows line number of current op and offset of
        # first op on following line, given offset of op as index
        lines = []
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
        return lines

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
            for _ in range(instruction_size(op, self.opc)):
                self.prev_op.append(offset)

    def find_jump_targets(self, debug):
        """
        Detect all offsets in a byte code which are jump targets
        where we might insert a COME_FROM instruction.

        Return the list of offsets.

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
        self.except_targets = {}
        self.ignore_if = set()
        self.build_statement_indices()
        self.else_start = {}

        # Containers filled by detect_control_flow()
        self.not_continue = set()
        self.return_end_ifs = set()
        self.setup_loop_targets = {}  # target given setup_loop offset
        self.setup_loops = {}  # setup_loop offset given target

        targets = {}
        for i, inst in enumerate(self.insts):
            offset = inst.offset
            op = inst.opcode

            # Determine structures and fix jumps in Python versions
            # since 2.3
            self.detect_control_flow(offset, targets, i)

            if inst.has_arg:
                label = self.fixed_jumps.get(offset)
                oparg = inst.arg
                if (self.version >= 3.6 and
                    self.code[offset] == self.opc.EXTENDED_ARG):
                    j = xdis.next_offset(op, self.opc, offset)
                    next_offset = xdis.next_offset(op, self.opc, j)
                else:
                    next_offset = xdis.next_offset(op, self.opc, offset)

                if label is None:
                    if op in op3.hasjrel and op != self.opc.FOR_ITER:
                        label = next_offset + oparg
                    elif op in op3.hasjabs:
                        if op in self.jump_if_pop:
                            if oparg > offset:
                                label = oparg

                if label is not None and label != -1:
                    targets[label] = targets.get(label, []) + [offset]
            elif op == self.opc.END_FINALLY and offset in self.fixed_jumps:
                label = self.fixed_jumps[offset]
                targets[label] = targets.get(label, []) + [offset]
                pass

            pass # for loop

        # DEBUG:
        if debug in ('both', 'after'):
            import pprint as pp
            pp.pprint(self.structs)

        return targets

    def build_statement_indices(self):
        code = self.code
        start = 0
        end = codelen = len(code)

        # Compose preliminary list of indices with statements,
        # using plain statement opcodes
        prelim = self.all_instr(start, end, self.statement_opcodes)

        # Initialize final container with statements with
        # preliminary data
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
                    i += instruction_size(code[i], self.opc)

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
                # FIXME: 0 isn't always correct
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

    def detect_control_flow(self, offset, targets, inst_index):
        """
        Detect type of block structures and their boundaries to fix optimized jumps
        in python2.3+
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
                jump_back = self.last_instr(start, end, self.opc.RETURN_VALUE)
                if not jump_back:
                    return

                jump_back += 2  # FIXME ???
                if_offset = None
                if code[self.prev_op[next_line_byte]] not in self.pop_jump_tf:
                    if_offset = self.prev[next_line_byte]
                if if_offset:
                    loop_type = 'while'
                    self.ignore_if.add(if_offset)
                else:
                    loop_type = 'for'
                target = next_line_byte
                end = xdis.next_offset(code[jump_back], self.opc, jump_back)
            else:
                if self.get_target(jump_back) >= next_line_byte:
                    jump_back = self.last_instr(start, end, self.opc.JUMP_ABSOLUTE, start, False)

                # This is wrong for 3.6+
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
                    if next_line_byte < len(code):
                        test_inst = self.insts[self.offset2inst_index[next_line_byte]-1]
                        if test_inst.offset == offset:
                            loop_type = 'while 1'
                        elif test_inst.opcode in self.opc.JUMP_OPs:
                            self.ignore_if.add(test_inst.offset)
                            test_target = self.get_target(test_inst.offset)
                            if test_target > (jump_back+3):
                                jump_back = test_target
                                pass
                            pass
                        pass
                self.not_continue.add(jump_back)
            self.loops.append(target)
            self.structs.append({'type': loop_type + '-loop',
                                 'start': target,
                                 'end':   jump_back})
            after_jump_offset = xdis.next_offset(code[jump_back], self.opc, jump_back)
            if after_jump_offset != end:
                self.structs.append({'type': loop_type + '-else',
                                     'start': after_jump_offset,
                                     'end':   end})
        elif op in self.pop_jump_tf:
            start   = offset + instruction_size(op, self.opc)
            target  = self.insts[inst_index].argval
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
            pretarget = self.get_inst(prev_op[target])

            if (pretarget.opcode in self.pop_jump_if_pop and
                (target > offset) and pretarget.offset != offset):

                # FIXME: hack upon hack...
                # In some cases the pretarget can be a jump to the next instruction
                # and these aren't and/or's either. We limit to 3.5+ since we experienced there
                # but it might be earlier versions, or might be a general principle.
                if self.version < 3.5 or pretarget.argval != target:
                    # FIXME: this is not accurate The commented out below
                    # is what it should be. However grammar rules right now
                    # assume the incorrect offsets.
                    # self.fixed_jumps[offset] = target
                    self.fixed_jumps[offset] = pretarget.offset
                    self.structs.append({'type': 'and/or',
                                         'start': start,
                                         'end': pretarget.offset})
                    return

            # The opcode *two* instructions before the target jump offset is important
            # in making a determination of what we have. Save that.
            pre_rtarget = prev_op[rtarget]

            # Is it an "and" inside an "if" or "while" block
            if op == self.opc.POP_JUMP_IF_FALSE and self.version < 3.6:

                # Search for another POP_JUMP_IF_FALSE targetting the same op,
                # in current statement, starting from current offset, and filter
                # everything inside inner 'or' jumps and midline ifs
                match = self.rem_or(start, self.next_stmt[offset],
                                    self.opc.POP_JUMP_IF_FALSE, target)

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
                            1 == len(self.remove_mid_line_ifs(self.rem_or(start, prev_op[pre_rtarget], self.pop_jump_tf, target)))):
                            pass
                        elif (code[prev_op[pre_rtarget]] == self.opc.RETURN_VALUE
                              and self.remove_mid_line_ifs([offset]) and
                              1 == (len(set(self.remove_mid_line_ifs(self.rem_or(start, prev_op[pre_rtarget],
                                                                                 self.pop_jump_tf, target))) |
                                    set(self.remove_mid_line_ifs(self.rem_or(start, prev_op[pre_rtarget],
                                                                             (self.opc.POP_JUMP_IF_FALSE,
                                                                              self.opc.POP_JUMP_IF_TRUE,
                                                                              self.opc.JUMP_ABSOLUTE),
                                                                             pre_rtarget, True)))))):
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
            if self.is_jump_forward(pre_rtarget):
                if_end = self.get_target(pre_rtarget)

                # If the jump target is back, we are looping
                if (if_end < pre_rtarget and
                    (code[prev_op[if_end]] == self.opc.SETUP_LOOP)):
                    if (if_end > start):
                        return

                end = self.restrict_to_parent(if_end, parent)

                self.structs.append({'type': 'if-then',
                                     'start': start,
                                     'end': pre_rtarget})

                # FIXME: add this
                # self.fixed_jumps[offset] = rtarget
                self.not_continue.add(pre_rtarget)

                if rtarget < end and (
                        code[rtarget] not in (self.opc.END_FINALLY,
                                              self.opc.JUMP_ABSOLUTE) and
                        code[prev_op[pre_rtarget]] not in (self.opc.POP_EXCEPT,
                                                        self.opc.END_FINALLY)):
                    self.structs.append({'type': 'else',
                                         'start': rtarget,
                                         'end': end})
                    self.else_start[rtarget] = end
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
                    # If we are at some sort of POP_JUMP_IF and the instruction before was
                    # COMPARE_OP exception-match, then pre_rtarget is not an end_if
                    if not (inst_index > 0 and self.insts[inst_index-1].argval == 'exception-match'):
                        self.return_end_ifs.add(pre_rtarget)
                else:
                    self.fixed_jumps[offset] = rtarget
                    self.not_continue.add(pre_rtarget)
            else:

                # FIXME: this is very convoluted and based on rather hacky
                # empirical evidence. It should go a way when
                # we have better control-flow analysis
                normal_jump = self.version >= 3.6
                if self.version == 3.5:
                    j = self.offset2inst_index[target]
                    if j+2 < len(self.insts) and self.insts[j+2].is_jump_target:
                        normal_jump = self.insts[j+1].opname == 'POP_BLOCK'

                if normal_jump:
                    # For now, we'll only tag forward jump.
                    if target > offset:
                        self.fixed_jumps[offset] = target
                        pass
                else:
                    # FIXME: This is probably a bug in < 3.5 and we should
                    # instead use the above code. But until we smoke things
                    # out we'll stick with it.
                    if rtarget > offset:
                        self.fixed_jumps[offset] = rtarget

        elif op == self.opc.SETUP_EXCEPT:
            target = self.get_target(offset)
            end    = self.restrict_to_parent(target, parent)
            self.fixed_jumps[offset] = end
        elif op == self.opc.POP_EXCEPT:
            next_offset = xdis.next_offset(op, self.opc, offset)
            target = self.get_target(next_offset)
            if target is None:
                from trepan.api import debug; debug()
            if target > next_offset:
                next_op = code[next_offset]
                if (self.opc.JUMP_ABSOLUTE == next_op and
                    self.opc.END_FINALLY != code[xdis.next_offset(next_op, self.opc, next_offset)]):
                    self.fixed_jumps[next_offset] = target
                    self.except_targets[target] = next_offset

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
                next_offset = xdis.next_offset(op, self.opc, offset)
                if (next_offset < len(code) and code[next_offset] == self.opc.JUMP_ABSOLUTE and
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
                        if code[i] in [op3.JUMP_FORWARD, op3.JUMP_ABSOLUTE]:
                            return
                        i = self.prev[i]
                    self.return_end_ifs.remove(rtarget_prev)
                pass
        return

    def is_jump_back(self, offset, extended_arg):
        """
        Return True if the code at offset is some sort of jump back.
        That is, it is ether "JUMP_FORWARD" or an absolute jump that
        goes forward.
        """
        if self.code[offset] != self.opc.JUMP_ABSOLUTE:
            return False
        return offset > self.get_target(offset, extended_arg)

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
                    assert self.code[self.prev_op[i]] in frozenset([self.opc.JUMP_ABSOLUTE,
                                                                    self.opc.JUMP_FORWARD,
                                                                    self.opc.RETURN_VALUE])
                    self.not_continue.add(self.prev_op[i])
                    return self.prev_op[i]
                count_END_FINALLY += 1
            elif op in self.setup_opts_no_loop:
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
        if self.version == 3.0:
            jump_true_op = self.opc.JUMP_IF_TRUE
        else:
            jump_true_op = self.opc.POP_JUMP_IF_TRUE
        pjit_offsets = self.all_instr(start, end, jump_true_op)
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
        tokens, customize = Scanner3(PYTHON_VERSION).ingest(co)
        for t in tokens:
            print(t)
    else:
        print("Need to be Python 3.2 or greater to demo; I am %s." %
              PYTHON_VERSION)
    pass
