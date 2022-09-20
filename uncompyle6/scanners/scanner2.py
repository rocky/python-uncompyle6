#  Copyright (c) 2015-2022 by Rocky Bernstein
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

from copy import copy

from xdis import code2num, iscode, op_has_argument, instruction_size
from xdis.bytecode import _get_const_info
from uncompyle6.scanner import Scanner, Token


class Scanner2(Scanner):
    def __init__(self, version, show_asm=None, is_pypy=False):
        Scanner.__init__(self, version, show_asm, is_pypy)
        self.pop_jump_if = frozenset([self.opc.PJIF, self.opc.PJIT])
        self.jump_forward = frozenset([self.opc.JUMP_ABSOLUTE, self.opc.JUMP_FORWARD])
        # This is the 2.5+ default
        # For <2.5 it is <generator expression>
        self.genexpr_name = "<genexpr>"
        self.load_asserts = set([])

        # Create opcode classification sets
        # Note: super initilization above initializes self.opc

        # Ops that start SETUP_ ... We will COME_FROM with these names
        # Some blocks and END_ statements. And they can start
        # a new statement

        self.statement_opcodes = frozenset(
            [
                self.opc.SETUP_LOOP,
                self.opc.BREAK_LOOP,
                self.opc.SETUP_FINALLY,
                self.opc.END_FINALLY,
                self.opc.SETUP_EXCEPT,
                self.opc.POP_BLOCK,
                self.opc.STORE_FAST,
                self.opc.DELETE_FAST,
                self.opc.STORE_DEREF,
                self.opc.STORE_GLOBAL,
                self.opc.DELETE_GLOBAL,
                self.opc.STORE_NAME,
                self.opc.DELETE_NAME,
                self.opc.STORE_ATTR,
                self.opc.DELETE_ATTR,
                self.opc.STORE_SUBSCR,
                self.opc.DELETE_SUBSCR,
                self.opc.RETURN_VALUE,
                self.opc.RAISE_VARARGS,
                self.opc.POP_TOP,
                self.opc.PRINT_EXPR,
                self.opc.PRINT_ITEM,
                self.opc.PRINT_NEWLINE,
                self.opc.PRINT_ITEM_TO,
                self.opc.PRINT_NEWLINE_TO,
                self.opc.CONTINUE_LOOP,
                self.opc.JUMP_ABSOLUTE,
                self.opc.EXEC_STMT,
            ]
        )

        # Opcodes that can start a "store" non-terminal.
        # FIXME: JUMP_ABSOLUTE is weird. What's up with that?
        self.designator_ops = frozenset(
            [
                self.opc.STORE_FAST,
                self.opc.STORE_NAME,
                self.opc.STORE_GLOBAL,
                self.opc.STORE_DEREF,
                self.opc.STORE_ATTR,
                self.opc.STORE_SLICE_0,
                self.opc.STORE_SLICE_1,
                self.opc.STORE_SLICE_2,
                self.opc.STORE_SLICE_3,
                self.opc.STORE_SUBSCR,
                self.opc.UNPACK_SEQUENCE,
                self.opc.JUMP_ABSOLUTE,
            ]
        )

        # Python 2.7 has POP_JUMP_IF_{TRUE,FALSE}_OR_POP but < 2.7 doesn't
        # Add an empty set make processing more uniform.
        self.pop_jump_if_or_pop = frozenset([])

        # opcodes with expect a variable number pushed values whose
        # count is in the opcode. For parsing we generally change the
        # opcode name to include that number.
        self.varargs_ops = frozenset(
            [
                self.opc.BUILD_LIST,
                self.opc.BUILD_TUPLE,
                self.opc.BUILD_SLICE,
                self.opc.UNPACK_SEQUENCE,
                self.opc.MAKE_FUNCTION,
                self.opc.CALL_FUNCTION,
                self.opc.MAKE_CLOSURE,
                self.opc.CALL_FUNCTION_VAR,
                self.opc.CALL_FUNCTION_KW,
                self.opc.CALL_FUNCTION_VAR_KW,
                self.opc.DUP_TOPX,
                self.opc.RAISE_VARARGS,
            ]
        )

    @staticmethod
    def extended_arg_val(arg):
        """Return integer value of an EXTENDED_ARG operand.
        In Python2 this always the operand value shifted 16 bits since
        the operand is always 2 bytes. In Python 3.6+ this changes to one byte.
        """
        return arg << long(16)

    @staticmethod
    def unmangle_name(name, classname):
        """Remove __ from the end of _name_ if it starts with __classname__
        return the "unmangled" name.
        """
        if name.startswith(classname) and name[-2:] != "__":
            return name[len(classname) - 2 :]
        return name

    @classmethod
    def unmangle_code_names(self, co, classname):
        """Remove __ from the end of _name_ if it starts with __classname__
        return the "unmangled" name.
        """
        if classname:
            classname = "_" + classname.lstrip("_") + "__"

            if hasattr(co, "co_cellvars"):
                free = [
                    self.unmangle_name(name, classname)
                    for name in (co.co_cellvars + co.co_freevars)
                ]
            else:
                free = ()

            names = [self.unmangle_name(name, classname) for name in co.co_names]
            varnames = [self.unmangle_name(name, classname) for name in co.co_varnames]
        else:
            if hasattr(co, "co_cellvars"):
                free = co.co_cellvars + co.co_freevars
            else:
                free = ()
            names = co.co_names
            varnames = co.co_varnames
        return free, names, varnames

    def ingest(self, co, classname=None, code_objects={}, show_asm=None):
        """
        Create "tokens" the bytecode of an Python code object. Largely these
        are the opcode name, but in some cases that has been modified to make parsing
        easier.
        returning a list of uncompyle6 Token's.

        Some transformations are made to assist the deparsing grammar:
           -  various types of LOAD_CONST's are categorized in terms of what they load
           -  COME_FROM instructions are added to assist parsing control structures
           -  operands with stack argument counts or flag masks are appended to the opcode name, e.g.:
              *  BUILD_LIST, BUILD_SET
              *  MAKE_FUNCTION and FUNCTION_CALLS append the number of positional arguments
           -  EXTENDED_ARGS instructions are removed

        Also, when we encounter certain tokens, we add them to a set which will cause custom
        grammar rules. Specifically, variable arg tokens like MAKE_FUNCTION or BUILD_LIST
        cause specific rules for the specific number of arguments they take.
        """
        if not show_asm:
            show_asm = self.show_asm

        bytecode = self.build_instructions(co)

        # show_asm = 'after'
        if show_asm in ("both", "before"):
            for instr in bytecode.get_instructions(co):
                print(instr.disassemble())

        # list of tokens/instructions
        new_tokens = []

        # "customize" is in the process of going away here
        customize = {}
        if self.is_pypy:
            customize["PyPy"] = 0

        codelen = len(self.code)

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
            # Below we use the heuristic that an "sssert" is preceded by a POP_JUMP.
            # however we could also use followed by RAISE_VARARGS
            # or for PyPy there may be a JUMP_IF_NOT_DEBUG before.
            # FIXME: remove uses of PJIF, and PJIT
            if self.is_pypy:
                have_pop_jump = self.code[i] in (self.opc.PJIF, self.opc.PJIT)
            else:
                have_pop_jump = self.code[i] == self.opc.PJIT

            if have_pop_jump and self.code[i + 3] == self.opc.LOAD_GLOBAL:
                if names[self.get_argument(i + 3)] == "AssertionError":
                    self.load_asserts.add(i + 3)

        # Get jump targets
        # Format: {target offset: [jump offsets]}
        load_asserts_save = copy(self.load_asserts)
        jump_targets = self.find_jump_targets(show_asm)
        self.load_asserts = load_asserts_save
        # print("XXX2", jump_targets)

        last_stmt = self.next_stmt[0]
        i = self.next_stmt[last_stmt]
        replace = {}
        while i < codelen - 1:
            if self.lines[last_stmt].next > i:
                # Distinguish "print ..." from "print ...,"
                if self.code[last_stmt] == self.opc.PRINT_ITEM:
                    if self.code[i] == self.opc.PRINT_ITEM:
                        replace[i] = "PRINT_ITEM_CONT"
                    elif self.code[i] == self.opc.PRINT_NEWLINE:
                        replace[i] = "PRINT_NEWLINE_CONT"
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
                for jump_offset in sorted(jump_targets[offset], reverse=True):
                    # if jump_offset == last_offset:
                    #     continue
                    # last_offset = jump_offset
                    come_from_name = "COME_FROM"
                    op_name = self.opname_for_offset(jump_offset)
                    if op_name.startswith("SETUP_") and self.version[:2] == (2, 7):
                        come_from_type = op_name[len("SETUP_") :]
                        if come_from_type not in ("LOOP", "EXCEPT"):
                            come_from_name = "COME_FROM_%s" % come_from_type
                        pass
                    new_tokens.append(
                        Token(
                            come_from_name,
                            jump_offset,
                            repr(jump_offset),
                            offset="%s_%d" % (offset, jump_idx),
                            has_arg=True,
                        )
                    )
                    jump_idx += 1
                    pass

            op = self.code[offset]
            op_name = self.op_name(op)

            oparg = None
            pattr = None
            has_arg = op_has_argument(op, self.opc)
            if has_arg:
                oparg = self.get_argument(offset) + extended_arg
                extended_arg = 0
                if op == self.opc.EXTENDED_ARG:
                    extended_arg += self.extended_arg_val(oparg)
                    continue

                # Note: name used to match on rather than op since
                # BUILD_SET isn't in earlier Pythons.
                if op_name in (
                    "BUILD_LIST",
                    "BUILD_SET",
                ):
                    t = Token(
                        op_name, oparg, pattr, offset, self.linestarts.get(offset, None), op, has_arg, self.opc
                    )
                    collection_type = op_name.split("_")[1]
                    next_tokens = self.bound_collection_from_tokens(
                        new_tokens, t, len(new_tokens), "CONST_%s" % collection_type
                    )
                    if next_tokens is not None:
                        new_tokens = next_tokens
                        continue

                if op in self.opc.CONST_OPS:
                    const = co.co_consts[oparg]
                    if iscode(const):
                        oparg = const
                        if const.co_name == "<lambda>":
                            assert op_name == "LOAD_CONST"
                            op_name = "LOAD_LAMBDA"
                        elif const.co_name == "<genexpr>":
                            op_name = "LOAD_GENEXPR"
                        elif const.co_name == "<dictcomp>":
                            op_name = "LOAD_DICTCOMP"
                        elif const.co_name == "<setcomp>":
                            op_name = "LOAD_SETCOMP"
                        else:
                            op_name = "LOAD_CODE"
                        # verify() uses 'pattr' for comparison, since 'attr'
                        # now holds Code(const) and thus can not be used
                        # for comparison (todo: think about changing this)
                        # pattr = 'code_object @ 0x%x %s->%s' %\
                        # (id(const), const.co_filename, const.co_name)
                        pattr = "<code_object " + const.co_name + ">"
                    else:
                        if oparg < len(co.co_consts):
                            argval, _ = _get_const_info(oparg, co.co_consts)
                        # Why don't we use _ above for "pattr" rather than "const"?
                        # This *is* a little hoaky, but we have to coordinate with
                        # other parts like n_LOAD_CONST in pysource.py for example.
                        pattr = const
                        pass
                elif op in self.opc.NAME_OPS:
                    pattr = names[oparg]
                elif op in self.opc.JREL_OPS:
                    #  use instead: hasattr(self, 'patch_continue'): ?
                    if self.version[:2] == (2, 7):
                        self.patch_continue(new_tokens, offset, op)
                    pattr = repr(offset + 3 + oparg)
                elif op in self.opc.JABS_OPS:
                    # use instead: hasattr(self, 'patch_continue'): ?
                    if self.version[:2] == (2, 7):
                        self.patch_continue(new_tokens, offset, op)
                    pattr = repr(oparg)
                elif op in self.opc.LOCAL_OPS:
                    pattr = varnames[oparg]
                elif op in self.opc.COMPARE_OPS:
                    pattr = self.opc.cmp_op[oparg]
                elif op in self.opc.FREE_OPS:
                    pattr = free[oparg]

            if op in self.varargs_ops:
                # CE - Hack for >= 2.5
                #      Now all values loaded via LOAD_CLOSURE are packed into
                #      a tuple before calling MAKE_CLOSURE.
                if (
                    op == self.opc.BUILD_TUPLE
                    and self.code[self.prev[offset]] == self.opc.LOAD_CLOSURE
                ):
                    continue
                else:
                    if self.is_pypy and not oparg and op_name == "BUILD_MAP":
                        op_name = "BUILD_MAP_n"
                    else:
                        op_name = "%s_%d" % (op_name, oparg)
                        pass
                    # FIXME: Figure out why this is needed and remove.
                    customize[op_name] = oparg
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
                    op_name = "JUMP_BACK"

                    # 'Continue's include jumps to loops that are not
                    # and the end of a block which follow with POP_BLOCK and COME_FROM_LOOP.
                    # If the JUMP_ABSOLUTE is
                    #   either to a FOR_ITER or the instruction after a SETUP_LOOP
                    #   and it is followed by another JUMP_FORWARD
                    # then we'll take it as a "continue".
                    j = self.offset2inst_index.get(offset)

                    # EXTENDED_ARG doesn't appear in instructions,
                    # but is instead the next opcode folded into it, and has the offset
                    # of the EXTENDED_ARG. Therefor in self.offset2nist_index we'll find
                    # the instruction at the previous EXTENDED_ARG offset which is 3
                    # bytes back.
                    if j is None and offset > self.opc.ARG_MAX_VALUE:
                        j = self.offset2inst_index[offset - 3]

                    target_index = self.offset2inst_index[target]
                    is_continue = (
                        self.insts[target_index - 1].opname == "SETUP_LOOP"
                        and self.insts[j + 1].opname == "JUMP_FORWARD"
                    )
                    if is_continue:
                        op_name = "CONTINUE"
                    if offset in self.stmts and self.code[offset + 3] not in (
                        self.opc.END_FINALLY,
                        self.opc.POP_BLOCK,
                    ):
                        if (
                            (
                                offset in self.linestarts
                                and self.code[self.prev[offset]]
                                == self.opc.JUMP_ABSOLUTE
                            )
                            or self.code[target] == self.opc.FOR_ITER
                            or offset not in self.not_continue
                        ):
                            op_name = "CONTINUE"

            elif op == self.opc.LOAD_GLOBAL:
                if offset in self.load_asserts:
                    op_name = "LOAD_ASSERT"
            elif op == self.opc.RETURN_VALUE:
                if offset in self.return_end_ifs:
                    op_name = "RETURN_END_IF"

            linestart = self.linestarts.get(offset, None)

            if offset not in replace:
                new_tokens.append(
                    Token(
                        op_name, oparg, pattr, offset, linestart, op, has_arg, self.opc
                    )
                )
            else:
                new_tokens.append(
                    Token(
                        replace[offset],
                        oparg,
                        pattr,
                        offset,
                        linestart,
                        op,
                        has_arg,
                        self.opc,
                    )
                )
                pass
            pass

        if show_asm in ("both", "after"):
            for t in new_tokens:
                print(t.format(line_prefix=""))
            print()
        return new_tokens, customize

    def build_statement_indices(self):
        code = self.code
        start = 0
        end = len(code)

        stmt_opcode_seqs = frozenset(
            [
                (self.opc.PJIF, self.opc.JUMP_FORWARD),
                (self.opc.PJIF, self.opc.JUMP_ABSOLUTE),
                (self.opc.PJIT, self.opc.JUMP_FORWARD),
                (self.opc.PJIT, self.opc.JUMP_ABSOLUTE),
            ]
        )

        prelim = self.all_instr(start, end, self.statement_opcodes)

        stmts = self.stmts = set(prelim)
        pass_stmts = set()
        for seq in stmt_opcode_seqs:
            for i in self.op_range(start, end - (len(seq) + 1)):
                match = True
                for elem in seq:
                    if elem != code[i]:
                        match = False
                        break
                    i += instruction_size(code[i], self.opc)

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
                if target > s or (self.lines and self.lines[last_stmt].l_no == self.lines[s].l_no):
                    stmts.remove(s)
                    continue
                j = self.prev[s]
                while code[j] == self.opc.JUMP_ABSOLUTE:
                    j = self.prev[j]
                if (
                    self.version >= (2, 3) and self.opname_for_offset(j) == "LIST_APPEND"
                ):  # list comprehension
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
                if (
                    prev == self.opc.ROT_TWO
                    or self.version < (2, 7)
                    and prev
                    in (
                        self.opc.JUMP_IF_FALSE,
                        self.opc.JUMP_IF_TRUE,
                        self.opc.RETURN_VALUE,
                    )
                ):
                    stmts.remove(s)
                    continue
            elif code[s] in self.designator_ops:
                j = self.prev[s]
                while code[j] in self.designator_ops:
                    j = self.prev[j]
                if self.version > (2, 1) and code[j] == self.opc.FOR_ITER:
                    stmts.remove(s)
                    continue
            last_stmt = s
            slist += [s] * (s - i)
            i = s
        slist += [end] * (end - len(slist))

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
                if self.version < (2, 7) and self.code[jmp] in self.jump_forward:
                    self.not_continue.add(jmp)
                    jmp = self.get_target(jmp)
                    prev_offset = self.prev[except_match]
                    # COMPARE_OP argument should be "exception-match" or 10
                    if (
                        self.code[prev_offset] == self.opc.COMPARE_OP
                        and self.code[prev_offset + 1] != 10
                    ):
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
                    if self.version[:2] == (2, 7):
                        assert self.code[self.prev[i]] in self.jump_forward | frozenset(
                            [self.opc.RETURN_VALUE]
                        )
                    self.not_continue.add(self.prev[i])
                    return self.prev[i]
                count_END_FINALLY += 1
            elif op in self.setup_ops:
                count_SETUP_ += 1

    def detect_control_flow(self, offset, op, extended_arg):
        """
        Detect type of block structures and their boundaries to fix optimized jumps
        in python2.3+
        """

        code = self.code

        # Detect parent structure
        parent = self.structs[0]
        start = parent["start"]
        end = parent["end"]
        next_line_byte = end

        # Pick inner-most parent for our offset
        for struct in self.structs:
            current_start = struct["start"]
            current_end = struct["end"]
            if (current_start <= offset < current_end) and (
                current_start >= start and current_end <= end
            ):
                start = current_start
                end = current_end
                parent = struct

        if op == self.opc.SETUP_LOOP:
            # We categorize loop types: 'for', 'while', 'while 1' with
            # possibly suffixes '-loop' and '-else'
            # Try to find the jump_back instruction of the loop.
            # It could be a return instruction.

            inst = self.insts[self.offset2inst_index[offset]]
            start += instruction_size(op, self.opc)
            setup_target = inst.argval
            loop_end_offset = self.restrict_to_parent(setup_target, parent)
            self.setup_loop_targets[offset] = setup_target
            self.setup_loops[setup_target] = offset

            if setup_target != loop_end_offset:
                self.fixed_jumps[offset] = loop_end_offset

            if self.lines:
                (line_no, next_line_byte) = self.lines[offset]

            # jump_back_offset is the instruction after the SETUP_LOOP
            # where we iterate back to.
            jump_back_offset = self.last_instr(
                start, loop_end_offset, self.opc.JUMP_ABSOLUTE, next_line_byte, False
            )

            if jump_back_offset:
                # Account for the fact that < 2.7 has an explicit
                # POP_TOP instruction in the equivalate POP_JUMP_IF
                # construct
                if self.version < (2, 7):
                    jump_forward_offset = jump_back_offset + 4
                    return_val_offset1 = self.prev[
                        self.prev[self.prev[loop_end_offset]]
                    ]
                    # Is jump back really "back"?
                    jump_target = self.get_target(
                        jump_back_offset, code[jump_back_offset]
                    )
                    if jump_target > jump_back_offset or code[jump_back_offset + 3] in [
                        self.opc.JUMP_FORWARD,
                        self.opc.JUMP_ABSOLUTE,
                    ]:
                        jump_back_offset = None
                        pass
                else:
                    jump_forward_offset = jump_back_offset + 3
                    return_val_offset1 = self.prev[self.prev[loop_end_offset]]

            if (
                jump_back_offset
                and jump_back_offset != self.prev[loop_end_offset]
                and code[jump_forward_offset] in self.jump_forward
            ):
                if code[self.prev[loop_end_offset]] == self.opc.RETURN_VALUE or (
                    code[self.prev[loop_end_offset]] == self.opc.POP_BLOCK
                    and code[return_val_offset1] == self.opc.RETURN_VALUE
                ):
                    jump_back_offset = None

            if not jump_back_offset:
                # loop suite ends in return
                # scanner26 of wbiti had:
                # jump_back_offset = self.last_instr(start, loop_end_offset, self.opc.JUMP_ABSOLUTE, start, False)
                jump_back_offset = self.last_instr(
                    start, loop_end_offset, self.opc.RETURN_VALUE
                )
                if not jump_back_offset:
                    return
                jump_back_offset += 1

                if_offset = None
                if self.version < (2, 7):
                    # Look for JUMP_IF POP_TOP ...
                    if code[self.prev[next_line_byte]] == self.opc.POP_TOP and (
                        code[self.prev[self.prev[next_line_byte]]] in self.pop_jump_if
                    ):
                        if_offset = self.prev[self.prev[next_line_byte]]
                elif code[self.prev[next_line_byte]] in self.pop_jump_if:
                    # Look for POP_JUMP_IF ...
                    if_offset = self.prev[next_line_byte]
                if if_offset:
                    loop_type = "while"
                    self.ignore_if.add(if_offset)
                    if self.version < (2, 7) and (
                        code[self.prev[jump_back_offset]] == self.opc.RETURN_VALUE
                    ):
                        self.ignore_if.add(self.prev[jump_back_offset])
                        pass
                    pass
                else:
                    loop_type = "for"
                setup_target = next_line_byte
                loop_end_offset = jump_back_offset + 3
            else:
                # We have a loop with a jump-back instruction
                if self.get_target(jump_back_offset) >= next_line_byte:
                    jump_back_offset = self.last_instr(
                        start, loop_end_offset, self.opc.JUMP_ABSOLUTE, start, False
                    )
                if (
                    loop_end_offset > jump_back_offset + 4
                    and code[loop_end_offset] in self.jump_forward
                ):
                    if code[jump_back_offset + 4] in self.jump_forward:
                        if self.get_target(jump_back_offset + 4) == self.get_target(
                            loop_end_offset
                        ):
                            self.fixed_jumps[offset] = jump_back_offset + 4
                            loop_end_offset = jump_back_offset + 4
                elif setup_target < offset:
                    self.fixed_jumps[offset] = jump_back_offset + 4
                    loop_end_offset = jump_back_offset + 4

                setup_target = self.get_target(jump_back_offset, self.opc.JUMP_ABSOLUTE)

                if self.version > (2, 1) and code[setup_target] in (
                    self.opc.FOR_ITER,
                    self.opc.GET_ITER,
                ):
                    loop_type = "for"
                else:
                    loop_type = "while"
                    # Look for a test condition immediately after the
                    # SETUP_LOOP while
                    if (
                        self.version < (2, 7)
                        and self.code[self.prev[next_line_byte]] == self.opc.POP_TOP
                    ):
                        test_op_offset = self.prev[self.prev[next_line_byte]]
                    else:
                        test_op_offset = self.prev[next_line_byte]

                    if test_op_offset == offset:
                        loop_type = "while 1"
                    elif self.code[test_op_offset] in self.opc.JUMP_OPs:
                        test_target = self.get_target(test_op_offset)

                        self.ignore_if.add(test_op_offset)

                        if test_target > (jump_back_offset + 3):
                            jump_back_offset = test_target
                self.not_continue.add(jump_back_offset)
            self.loops.append(setup_target)
            self.structs.append(
                {
                    "type": loop_type + "-loop",
                    "start": setup_target,
                    "end": jump_back_offset,
                }
            )
            if jump_back_offset + 3 != loop_end_offset:
                self.structs.append(
                    {
                        "type": loop_type + "-else",
                        "start": jump_back_offset + 3,
                        "end": loop_end_offset,
                    }
                )
        elif op == self.opc.SETUP_EXCEPT:
            start = offset + instruction_size(op, self.opc)
            target = self.get_target(offset, op)
            end_offset = self.restrict_to_parent(target, parent)
            if target != end_offset:
                self.fixed_jumps[offset] = end_offset
                # print target, end, parent
            # Add the try block
            self.structs.append(
                {"type": "try", "start": start - 3, "end": end_offset - 4}
            )
            # Now isolate the except and else blocks
            end_else = start_else = self.get_target(self.prev[end_offset])

            end_finally_offset = end_offset
            setup_except_nest = 0
            while end_finally_offset < len(self.code):
                if self.code[end_finally_offset] == self.opc.END_FINALLY:
                    if setup_except_nest == 0:
                        break
                    else:
                        setup_except_nest -= 1
                elif self.code[end_finally_offset] == self.opc.SETUP_EXCEPT:
                    setup_except_nest += 1
                end_finally_offset += instruction_size(
                    code[end_finally_offset], self.opc
                )
                pass

            # Add the except blocks
            i = end_offset
            while i < len(self.code) and i < end_finally_offset:
                jmp = self.next_except_jump(i)
                if jmp is None:  # check
                    i = self.next_stmt[i]
                    continue
                if self.code[jmp] == self.opc.RETURN_VALUE:
                    self.structs.append({"type": "except", "start": i, "end": jmp + 1})
                    i = jmp + 1
                else:
                    target = self.get_target(jmp)
                    if target != start_else:
                        end_else = self.get_target(jmp)
                    if self.code[jmp] == self.opc.JUMP_FORWARD:
                        if self.version <= (2, 6):
                            self.fixed_jumps[jmp] = target
                        else:
                            self.fixed_jumps[jmp] = -1
                    self.structs.append({"type": "except", "start": i, "end": jmp})
                    i = jmp + 3

            # Add the try-else block
            if end_else != start_else:
                r_end_else = self.restrict_to_parent(end_else, parent)
                # May be able to drop the 2.7 test.
                if self.version[:2] == (2, 7):
                    self.structs.append(
                        {"type": "try-else", "start": i + 1, "end": r_end_else}
                    )
                    self.fixed_jumps[i] = r_end_else
            else:
                self.fixed_jumps[i] = i + 1

        elif op in self.pop_jump_if:
            target = self.get_target(offset, op)
            rtarget = self.restrict_to_parent(target, parent)

            # Do not let jump to go out of parent struct bounds
            if target != rtarget and parent["type"] == "and/or":
                self.fixed_jumps[offset] = rtarget
                return

            jump_if_offset = offset

            start = offset + 3
            pre = self.prev

            # Does this jump to right after another conditional jump that is
            # not myself?  If so, it's part of a larger conditional.
            # rocky: if we have a conditional jump to the next instruction, then
            # possibly I am "skipping over" a "pass" or null statement.

            test_target = target
            if self.version < (2, 7):
                # Before 2.7 we have to deal with the fact that there is an extra
                # POP_TOP that is logically associated with the JUMP_IF's (even though
                # the instance set is called "self.pop_jump_if")
                if code[pre[test_target]] == self.opc.POP_TOP:
                    test_target = pre[test_target]
                test_set = self.pop_jump_if
            else:
                test_set = self.pop_jump_if_or_pop | self.pop_jump_if

            if code[pre[test_target]] in test_set and target > offset:
                # We have POP_JUMP_IF... target
                # ...
                # pre: POP_JUMP_IF ...
                # target: ...
                #
                # We will take that as either as "and" or "or".
                self.fixed_jumps[offset] = pre[target]
                self.structs.append(
                    {"type": "and/or", "start": start, "end": pre[target]}
                )
                return

            # The instruction offset just before the target jump offset is important
            # in making a determination of what we have. Save that.
            pre_rtarget = pre[rtarget]

            # Is it an "and" inside an "if" or "while" block
            if op == self.opc.PJIF:

                # Search for other POP_JUMP_IF_...'s targetting the
                # same target, of the current POP_JUMP_... instruction,
                # starting from current offset, and filter everything inside inner 'or'
                # jumps and mid-line ifs
                match = self.rem_or(
                    start, self.next_stmt[offset], self.opc.PJIF, target
                )

                # If we still have any offsets in set, start working on it
                if match:
                    if (
                        code[pre_rtarget] in self.jump_forward
                        and pre_rtarget not in self.stmts
                        and self.restrict_to_parent(
                            self.get_target(pre_rtarget), parent
                        )
                        == rtarget
                    ):
                        if (
                            code[pre[pre_rtarget]] == self.opc.JUMP_ABSOLUTE
                            and self.remove_mid_line_ifs([offset])
                            and target == self.get_target(pre[pre_rtarget])
                            and (
                                pre[pre_rtarget] not in self.stmts
                                or self.get_target(pre[pre_rtarget]) > pre[pre_rtarget]
                            )
                            and 1
                            == len(
                                self.remove_mid_line_ifs(
                                    self.rem_or(
                                        start,
                                        pre[pre_rtarget],
                                        self.pop_jump_if,
                                        target,
                                    )
                                )
                            )
                        ):
                            pass
                        elif (
                            code[pre[pre_rtarget]] == self.opc.RETURN_VALUE
                            and self.remove_mid_line_ifs([offset])
                            and 1
                            == (
                                len(
                                    set(
                                        self.remove_mid_line_ifs(
                                            self.rem_or(
                                                start,
                                                pre[pre_rtarget],
                                                self.pop_jump_if,
                                                target,
                                            )
                                        )
                                    )
                                    | set(
                                        self.remove_mid_line_ifs(
                                            self.rem_or(
                                                start,
                                                pre[pre_rtarget],
                                                (
                                                    self.opc.PJIF,
                                                    self.opc.PJIT,
                                                    self.opc.JUMP_ABSOLUTE,
                                                ),
                                                pre_rtarget,
                                                True,
                                            )
                                        )
                                    )
                                )
                            )
                        ):
                            pass
                        else:
                            fix = None
                            jump_ifs = self.all_instr(
                                start, self.next_stmt[offset], self.opc.PJIF
                            )
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
                        if self.version < (2, 7) and parent["type"] in (
                            "root",
                            "for-loop",
                            "if-then",
                            "else",
                            "try",
                        ):
                            self.fixed_jumps[offset] = rtarget
                        else:
                            # note test for < 2.7 might be superflous although informative
                            # for 2.7 a different branch is taken and the below code is handled
                            # under: elif op in self.pop_jump_if_or_pop
                            # below
                            self.fixed_jumps[offset] = match[-1]
                        return
            else:  # op != self.opc.PJIT
                if self.version < (2, 7) and code[offset + 3] == self.opc.POP_TOP:
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
                elif code[next] in self.jump_forward and target == self.get_target(
                    next
                ):
                    if code[pre[next]] == self.opc.PJIF:
                        if (
                            code[next] == self.opc.JUMP_FORWARD
                            or target != rtarget
                            or code[pre[pre_rtarget]]
                            not in (self.opc.JUMP_ABSOLUTE, self.opc.RETURN_VALUE)
                        ):
                            self.fixed_jumps[offset] = pre[next]
                            return
                elif (
                    code[next] == self.opc.JUMP_ABSOLUTE
                    and code[target] in self.jump_forward
                ):
                    next_target = self.get_target(next)
                    if self.get_target(target) == next_target:
                        self.fixed_jumps[offset] = pre[next]
                        return
                    elif code[next_target] in self.jump_forward and self.get_target(
                        next_target
                    ) == self.get_target(target):
                        self.fixed_jumps[offset] = pre[next]
                        return

            # don't add a struct for a while test, it's already taken care of
            if offset in self.ignore_if:
                return

            if self.version == (2, 7):
                if (
                    code[pre_rtarget] == self.opc.JUMP_ABSOLUTE
                    and pre_rtarget in self.stmts
                    and pre_rtarget != offset
                    and pre[pre_rtarget] != offset
                ):
                    if (
                        code[rtarget] == self.opc.JUMP_ABSOLUTE
                        and code[rtarget + 3] == self.opc.POP_BLOCK
                    ):
                        if code[pre[pre_rtarget]] != self.opc.JUMP_ABSOLUTE:
                            pass
                        elif self.get_target(pre[pre_rtarget]) != target:
                            pass
                        else:
                            rtarget = pre_rtarget
                    else:
                        rtarget = pre_rtarget
                    pre_rtarget = pre[rtarget]

            # Does the "jump if" jump beyond a jump op?
            # That is, we have something like:
            #  POP_JUMP_IF_FALSE HERE
            #  ...
            # JUMP_FORWARD
            # HERE:
            #
            # If so, this can be a block inside an "if" statement
            # or a conditional assignment like:
            #   x = 1 if x else 2
            #
            # There are other situations we may need to consider, like
            # if the condition jump is to a forward location.
            # Also the existence of a jump to the instruction after "END_FINALLY"
            # will distinguish "try/else" from "try".
            code_pre_rtarget = code[pre_rtarget]

            if code_pre_rtarget in self.jump_forward:
                if_end = self.get_target(pre_rtarget)

                # Is this a loop and not an "if" statment?
                if (if_end < pre_rtarget) and (pre[if_end] in self.setup_loop_targets):

                    if if_end > start:
                        return
                    else:
                        # We still have the case in 2.7 that the next instruction
                        # is a jump to a SETUP_LOOP target.
                        next_offset = target + instruction_size(
                            self.code[target], self.opc
                        )
                        next_op = self.code[next_offset]
                        if self.op_name(next_op) == "JUMP_FORWARD":
                            jump_target = self.get_target(next_offset, next_op)
                            if jump_target in self.setup_loops:
                                self.structs.append(
                                    {
                                        "type": "while-loop",
                                        "start": jump_if_offset,
                                        "end": jump_target,
                                    }
                                )
                                self.fixed_jumps[jump_if_offset] = jump_target
                                return

                end_offset = self.restrict_to_parent(if_end, parent)

                if_then_maybe = None

                if (2, 2) <= self.version <= (2, 6):
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

                    if self.opname_for_offset(jump_if_offset).startswith("JUMP_IF"):
                        jump_if_target = code[jump_if_offset + 1]
                        if (
                            self.opname_for_offset(jump_if_target + jump_if_offset + 3)
                            == "POP_TOP"
                        ):
                            jump_inst = jump_if_target + jump_if_offset
                            jump_offset = code[jump_inst + 1]
                            jump_op = self.opname_for_offset(jump_inst)
                            if jump_op == "JUMP_FORWARD" and jump_offset == 1:
                                self.structs.append(
                                    {
                                        "type": "if-then",
                                        "start": start - 3,
                                        "end": pre_rtarget,
                                    }
                                )
                                self.thens[start] = end_offset
                            elif jump_op == "JUMP_ABSOLUTE":
                                if_then_maybe = {
                                    "type": "if-then",
                                    "start": start - 3,
                                    "end": pre_rtarget,
                                }

                elif self.version[:2] == (2, 7):
                    self.structs.append(
                        {"type": "if-then", "start": start - 3, "end": pre_rtarget}
                    )

                # FIXME: this is yet another case were we need dominators.
                if pre_rtarget not in self.linestarts or self.version < (2, 7):
                    self.not_continue.add(pre_rtarget)

                if rtarget < end_offset:
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
                    if if_then_maybe and jump_op == "JUMP_ABSOLUTE":
                        jump_target = self.get_target(jump_inst, code[jump_inst])
                        if self.opname_for_offset(end_offset) == "JUMP_FORWARD":
                            end_target = self.get_target(end_offset, code[end_offset])
                            if jump_target == end_target:
                                self.structs.append(if_then_maybe)
                                self.thens[start] = end_offset

                    self.structs.append(
                        {"type": "else", "start": rtarget, "end": end_offset}
                    )
            elif code_pre_rtarget == self.opc.RETURN_VALUE:
                if self.version[:2] == (2, 7) or pre_rtarget not in self.ignore_if:
                    # Below, 10 is exception-match. If there is an exception
                    # match in the compare, then this is an exception
                    # clause not an if-then clause
                    if (
                        self.code[self.prev[offset]] != self.opc.COMPARE_OP
                        or self.code[self.prev[offset] + 1] != 10
                    ):
                        self.structs.append(
                            {"type": "if-then", "start": start, "end": rtarget}
                        )
                        self.thens[start] = rtarget
                        if (
                            self.version[:2] == (2, 7)
                            or code[pre_rtarget + 1] != self.opc.JUMP_FORWARD
                        ):
                            # The below is a big hack until we get
                            # better control flow analysis: disallow
                            # END_IF if the instruction before the
                            # END_IF instruction happens to be a jump
                            # target. In this case, probably what's
                            # gone on is that we messed up on the
                            # END_IF location and it should be the
                            # instruction before.
                            self.fixed_jumps[offset] = rtarget
                            if (
                                self.version[:2] == (2, 7)
                                and self.insts[
                                    self.offset2inst_index[pre[pre_rtarget]]
                                ].is_jump_target
                            ):
                                self.return_end_ifs.add(pre[pre_rtarget])
                                pass
                            else:
                                self.return_end_ifs.add(pre_rtarget)
                            pass
                        pass
                    pass

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
        self.structs = [{"type": "root", "start": 0, "end": n - 1}]
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
        self.thens = {}  # JUMP_IF's that separate the 'then' part of an 'if'

        targets = {}
        extended_arg = 0
        for offset in self.op_range(0, n):
            op = code[offset]

            if op == self.opc.EXTENDED_ARG:
                arg = code2num(code, offset + 1) | extended_arg
                extended_arg += self.extended_arg_val(arg)
                continue

            # Determine structures and fix jumps in Python versions
            # since 2.3
            self.detect_control_flow(offset, op, extended_arg)

            if op_has_argument(op, self.opc):
                label = self.fixed_jumps.get(offset)
                oparg = self.get_argument(offset)

                if label is None:
                    if op in self.opc.JREL_OPS and self.op_name(op) != "FOR_ITER":
                        # if (op in self.opc.JREL_OPS and
                        #     (self.version < 2.0 or op != self.opc.FOR_ITER)):
                        label = offset + 3 + oparg
                    elif self.version[:2] == (2, 7) and op in self.opc.JABS_OPS:
                        if op in (
                            self.opc.JUMP_IF_FALSE_OR_POP,
                            self.opc.JUMP_IF_TRUE_OR_POP,
                        ):
                            if oparg > offset:
                                label = oparg
                                pass
                            pass

                # FIXME FIXME FIXME
                # All the conditions are horrible, and I am not sure I
                # undestand fully what's going l
                # We REALLY REALLY  need a better way to handle control flow
                # Expecially for < 2.7
                if label is not None and label != -1:
                    if self.version[:2] == (2, 7):
                        # FIXME: rocky: I think we need something like this...
                        if label in self.setup_loops:
                            source = self.setup_loops[label]
                        else:
                            source = offset
                        targets[label] = targets.get(label, []) + [source]
                    elif not (
                        code[label] == self.opc.POP_TOP
                        and code[self.prev[label]] == self.opc.RETURN_VALUE
                    ):
                        # In Python < 2.7, don't add a COME_FROM, for:
                        #     ~RETURN_VALUE POP_TOP .. END_FINALLY
                        # or:
                        #     ~RETURN_VALUE POP_TOP .. POP_TOP END_FINALLY
                        skip_come_from = code[offset + 3] == self.opc.END_FINALLY or (
                            code[offset + 3] == self.opc.POP_TOP
                            and code[offset + 4] == self.opc.END_FINALLY
                        )

                        # The below is for special try/else handling
                        if skip_come_from and op == self.opc.JUMP_FORWARD:
                            skip_come_from = False

                        if not skip_come_from:
                            # FIXME: rocky: I think we need something like this...
                            if offset not in set(self.ignore_if):
                                if label in self.setup_loops:
                                    source = self.setup_loops[label]
                                else:
                                    source = offset
                                # FIXME: The grammar for 2.6 and before doesn't
                                # handle COME_FROM's from a loop inside if's
                                # It probably should.
                                if (
                                    self.version > (2, 6)
                                    or self.code[source] != self.opc.SETUP_LOOP
                                    or self.code[label] != self.opc.JUMP_FORWARD
                                ):
                                    targets[label] = targets.get(label, []) + [source]
                                pass
                            pass
                        pass
                    pass
            elif (
                op == self.opc.END_FINALLY
                and offset in self.fixed_jumps
                and self.version[:2] == (2, 7)
            ):
                label = self.fixed_jumps[offset]
                targets[label] = targets.get(label, []) + [offset]
                pass

            extended_arg = 0
            pass  # for loop

        # DEBUG:
        if debug in ("both", "after"):
            print(targets)
            import pprint as pp

            pp.pprint(self.structs)

        return targets

    def patch_continue(self, tokens, offset, op):
        if op in (self.opc.JUMP_FORWARD, self.opc.JUMP_ABSOLUTE):
            # FIXME: this is a hack to catch stuff like:
            #   for ...
            #     try: ...
            #     except: continue
            # the "continue" is not on a new line.
            n = len(tokens)
            if (
                n > 2
                and tokens[-1].kind == "JUMP_BACK"
                and self.code[offset + 3] == self.opc.END_FINALLY
            ):
                tokens[-1].kind = intern("CONTINUE")

    # FIXME: combine with scanner3.py code and put into scanner.py
    def rem_or(self, start, end, instr, target=None, include_beyond_target=False):
        """
        Find all <instr> in the block from start to end.
        <instr> is any python bytecode instruction or a list of opcodes
        If <instr> is an opcode with a target (like a jump), a target
        destination can be specified which must match precisely.

        Return a list with indexes to them or [] if none found.
        """

        assert start >= 0 and end <= len(self.code) and start <= end

        try:
            None in instr
        except:
            instr = [instr]

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
            tgt = self.get_target(pjit) - 3
            for i in instr_offsets:
                if i <= pjit or i >= tgt:
                    filtered.append(i)
            instr_offsets = filtered
            filtered = []
        return instr_offsets


if __name__ == "__main__":
    import inspect
    from xdis.version_info import PYTHON_VERSION_TRIPLE

    co = inspect.currentframe().f_code

    tokens, customize = Scanner2(PYTHON_VERSION_TRIPLE).ingest(co)
    for t in tokens:
            print(t)
    pass
