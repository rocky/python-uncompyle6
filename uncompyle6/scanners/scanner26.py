#  Copyright (c) 2015, 2016 by Rocky Bernstein
#  Copyright (c) 2005 by Dan Pascu <dan@windowmaker.org>
#  Copyright (c) 2000-2002 by hartmut Goebel <h.goebel@crazy-compilers.com>
"""
Python 2.6 bytecode scanner

This overlaps Python's 2.6's dis module, but it can be run from Python 3 and
other versions of Python. Also, we save token information for later
use in deparsing.
"""

import sys
from uncompyle6 import PYTHON3
if PYTHON3:
    intern = sys.intern

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
            self.opc.JUMP_ABSOLUTE
        ])

        # Python 2.7 has POP_JUMP_IF_{TRUE,FALSE}_OR_POP but < 2.7 doesn't
        # Add an empty set make processing more uniform.
        self.pop_jump_if_or_pop = frozenset([])
        return

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

        show_asm = self.show_asm if not show_asm else show_asm
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
                for jump_offset  in sorted(jump_targets[offset], reverse=True):
                    tokens.append(Token(
                        'COME_FROM', None, repr(jump_offset),
                        offset="%s_%d" % (offset, jump_idx),
                        has_arg = True))
                    jump_idx += 1
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
                        elif const.co_name == self.genexpr_name:
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
                    if op == self.opc.JUMP_FORWARD:
                        target = self.get_target(offset)
                        # FIXME: this is a hack to catch stuff like:
                        #   if x: continue
                        # the "continue" is not on a new line.
                        if len(tokens) and tokens[-1].type == 'JUMP_BACK':
                            tokens[-1].type = intern('CONTINUE')

                elif op in self.opc.hasjabs:
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
                if (self.version >= 2.5 and op == self.opc.BUILD_TUPLE and
                    self.code[self.prev[offset]] == self.opc.LOAD_CLOSURE):
                    continue
                else:
                    op_name = '%s_%d' % (op_name, oparg)
                    if op != self.opc.BUILD_SLICE:
                        customize[op_name] = oparg
            elif op == self.opc.JUMP_ABSOLUTE:
                # Further classify JUMP_ABSOLUTE into backward jumps
                # which are used in loops, and "CONTINUE" jumps which
                # may appear in a "continue" statement.  The loop-type
                # and continue-type jumps will help us classify loop
                # boundaries The continue-type jumps help us get
                # "continue" statements with would otherwise be turned
                # into a "pass" statement because JUMPs are sometimes
                # ignored in rules as just boundary overhead.
                target = self.get_target(offset)
                if target <= offset:
                    if (offset in self.stmts
                        and self.code[offset+3] not in (self.opc.END_FINALLY,
                                                          self.opc.POP_BLOCK)
                        and offset not in self.not_continue):
                        op_name = 'CONTINUE'
                    else:
                        op_name = 'JUMP_BACK'
                        # FIXME: this is a hack to catch stuff like:
                        #   if x: continue
                        # the "continue" is not on a new line.
                        if tokens[-1].type == 'JUMP_BACK':
                            # We need 'intern' since we have
                            # already have processed the previous
                            # token.
                            tokens[-1].type = intern('CONTINUE')

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
                    replace[offset], oparg, pattr, offset, linestart, op,
                    has_arg, self.opc))
                pass
            pass

        if show_asm in ('both', 'after'):
            for t in tokens:
                print(t.format(line_prefix='L.'))
            print()
        return tokens, customize

if __name__ == "__main__":
    from uncompyle6 import PYTHON_VERSION
    if PYTHON_VERSION == 2.6:
        import inspect
        co = inspect.currentframe().f_code
        tokens, customize = Scanner26(show_asm=True).ingest(co)
    else:
        print("Need to be Python 2.6 to demo; I am %s." %
              PYTHON_VERSION)
