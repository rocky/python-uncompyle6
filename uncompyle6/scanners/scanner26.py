#  Copyright (c) 2015-2017, 2021-2022 by Rocky Bernstein
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
Python 2.6 bytecode scanner

This overlaps Python's 2.6's dis module, but it can be run from Python 3 and
other versions of Python. Also, we save token information for later
use in deparsing.
"""

import uncompyle6.scanners.scanner2 as scan

# bytecode verification, verify(), uses JUMP_OPs from here
from xdis import iscode
from xdis.opcodes import opcode_26
from xdis.bytecode import _get_const_info

from uncompyle6.scanner import Token

JUMP_OPS = opcode_26.JUMP_OPS

class Scanner26(scan.Scanner2):
    def __init__(self, show_asm=False):
        super(Scanner26, self).__init__((2, 6), show_asm)

        # "setup" opcodes
        self.setup_ops = frozenset([
            self.opc.SETUP_EXCEPT, self.opc.SETUP_FINALLY,
            ])

        return

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

        # Container for tokens
        tokens = []

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
            if (self.code[i] == self.opc.JUMP_IF_TRUE and
                i + 4 < codelen and
                self.code[i+3] == self.opc.POP_TOP and
                self.code[i+4] == self.opc.LOAD_GLOBAL):
                if names[self.get_argument(i+4)] == 'AssertionError':
                    self.load_asserts.add(i+4)

        jump_targets = self.find_jump_targets(show_asm)
        # contains (code, [addrRefToCode])

        last_stmt = self.next_stmt[0]
        i = self.next_stmt[last_stmt]
        replace = {}
        while i < codelen - 1:
            if self.lines and self.lines[last_stmt].next > i:
                # Distinguish "print ..." from "print ...,"
                if self.code[last_stmt] == self.opc.PRINT_ITEM:
                    if self.code[i] == self.opc.PRINT_ITEM:
                        replace[i] = "PRINT_ITEM_CONT"
                    elif self.code[i] == self.opc.PRINT_NEWLINE:
                        replace[i] = "PRINT_NEWLINE_CONT"
            last_stmt = i
            i = self.next_stmt[i]

        extended_arg = 0
        i = -1
        for offset in self.op_range(0, codelen):
            i += 1
            op = self.code[offset]
            op_name = self.opname[op]
            oparg = None; pattr = None

            if offset in jump_targets:
                jump_idx = 0
                # We want to process COME_FROMs to the same offset to be in *descending*
                # offset order so we have the larger range or biggest instruction interval
                # last. (I think they are sorted in increasing order, but for safety
                # we sort them). That way, specific COME_FROM tags will match up
                # properly. For example, a "loop" with an "if" nested in it should have the
                # "loop" tag last so the grammar rule matches that properly.
                last_jump_offset = -1
                for jump_offset  in sorted(jump_targets[offset], reverse=True):
                    if jump_offset != last_jump_offset:
                        tokens.append(Token(
                            'COME_FROM', jump_offset, repr(jump_offset),
                            offset="%s_%d" % (offset, jump_idx),
                            has_arg = True))
                        jump_idx += 1
                        last_jump_offset = jump_offset
            elif offset in self.thens:
                tokens.append(Token(
                    'THEN', None, self.thens[offset],
                    offset="%s_0" % offset,
                    has_arg = True))

            has_arg = (op >= self.opc.HAVE_ARGUMENT)
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
                        tokens, t, len(tokens), "CONST_%s" % collection_type
                    )
                    if next_tokens is not None:
                        tokens = next_tokens
                        continue

                if op in self.opc.CONST_OPS:
                    const = co.co_consts[oparg]
                    if iscode(const):
                        oparg = const
                        if const.co_name == "<lambda>":
                            assert op_name == "LOAD_CONST"
                            op_name = "LOAD_LAMBDA"
                        elif const.co_name == self.genexpr_name:
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
                    pattr = repr(offset + 3 + oparg)
                    if op == self.opc.JUMP_FORWARD:
                        target = self.get_target(offset)
                        # FIXME: this is a hack to catch stuff like:
                        #   if x: continue
                        # the "continue" is not on a new line.
                        if len(tokens) and tokens[-1].kind == 'JUMP_BACK':
                            tokens[-1].kind = intern('CONTINUE')

                elif op in self.opc.JABS_OPS:
                    pattr = repr(oparg)
                elif op in self.opc.LOCAL_OPS:
                    if self.version < (1, 5):
                        pattr = names[oparg]
                    else:
                        pattr = varnames[oparg]
                elif op in self.opc.COMPARE_OPS:
                    pattr = self.opc.cmp_op[oparg]
                elif op in self.opc.FREE_OPS:
                    pattr = free[oparg]

            if op in self.varargs_ops:
                # CE - Hack for >= 2.5
                #      Now all values loaded via LOAD_CLOSURE are packed into
                #      a tuple before calling MAKE_CLOSURE.
                if (self.version >= (2, 5) and op == self.opc.BUILD_TUPLE and
                    self.code[self.prev[offset]] == self.opc.LOAD_CLOSURE):
                    continue
                else:
                    op_name = '%s_%d' % (op_name, oparg)
                    customize[op_name] = oparg
            elif self.version > (2, 0) and op == self.opc.CONTINUE_LOOP:
                customize[op_name] = 0
            elif op_name in """
                 CONTINUE_LOOP EXEC_STMT LOAD_LISTCOMP LOAD_SETCOMP
                  """.split():
                customize[op_name] = 0
            elif op == self.opc.JUMP_ABSOLUTE:
                # Further classify JUMP_ABSOLUTE into backward jumps
                # which are used in loops, and "CONTINUE" jumps which
                # may appear in a "continue" statement.  The loop-type
                # and continue-type jumps will help us classify loop
                # boundaries The continue-type jumps help us get
                # "continue" statements with would otherwise be turned
                # into a "pass" statement because JUMPs are sometimes
                # ignored in rules as just boundary overhead.  In
                # comprehensions we might sometimes classify JUMP_BACK
                # as CONTINUE, but that's okay since we add a grammar
                # rule for that.
                target = self.get_target(offset)
                if target <= offset:
                    op_name = 'JUMP_BACK'
                    if (offset in self.stmts
                        and self.code[offset+3] not in (self.opc.END_FINALLY,
                                                          self.opc.POP_BLOCK)):
                        if ((offset in self.linestarts and
                            tokens[-1].kind == 'JUMP_BACK')
                            or offset not in self.not_continue):
                            op_name = 'CONTINUE'
                    else:
                        # FIXME: this is a hack to catch stuff like:
                        #   if x: continue
                        # the "continue" is not on a new line.
                        if tokens[-1].kind == 'JUMP_BACK':
                            # We need 'intern' since we have
                            # already have processed the previous
                            # token.
                            tokens[-1].kind = intern('CONTINUE')

            elif op == self.opc.LOAD_GLOBAL:
                if offset in self.load_asserts:
                    op_name = "LOAD_ASSERT"
            elif op == self.opc.RETURN_VALUE:
                if offset in self.return_end_ifs:
                    op_name = "RETURN_END_IF"

            linestart = self.linestarts.get(offset, None)

            if offset not in replace:
                tokens.append(
                    Token(
                        op_name, oparg, pattr, offset, linestart, op, has_arg, self.opc
                    )
                )
            else:
                tokens.append(
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
            for t in tokens:
                print(t.format(line_prefix=""))
            print()
        return tokens, customize


if __name__ == "__main__":
    from xdis.version_info import PYTHON_VERSION_TRIPLE, version_tuple_to_str

    if PYTHON_VERSION_TRIPLE[:2] == (2, 6):
        import inspect

        co = inspect.currentframe().f_code  # type: ignore
        tokens, customize = Scanner26().ingest(co)
        for t in tokens:
            print(t.format())
        pass
    else:
        print("Need to be Python 2.6 to demo; I am version %s." % version_tuple_to_str())
