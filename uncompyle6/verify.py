#
# (C) Copyright 2015-2018, 2020-2021 by Rocky Bernstein
# (C) Copyright 2000-2002 by hartmut Goebel <h.goebel@crazy-compilers.com>
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
byte-code verification
"""

from __future__ import print_function

import operator, sys
import xdis.std as dis
from subprocess import call

import uncompyle6
from uncompyle6.scanner import Token as ScannerToken, get_scanner
from xdis import iscode, load_file, load_module, pretty_code_flags, PYTHON_MAGIC_INT

truediv = operator.truediv
from functools import reduce


def code_equal(a, b):
    return a.co_code == b.co_code


BIN_OP_FUNCS = {
    "BINARY_POWER": operator.pow,
    "BINARY_MULTIPLY": operator.mul,
    "BINARY_DIVIDE": truediv,
    "BINARY_FLOOR_DIVIDE": operator.floordiv,
    "BINARY_TRUE_DIVIDE": operator.truediv,
    "BINARY_MODULO": operator.mod,
    "BINARY_ADD": operator.add,
    "BINARY_SUBRACT": operator.sub,
    "BINARY_LSHIFT": operator.lshift,
    "BINARY_RSHIFT": operator.rshift,
    "BINARY_AND": operator.and_,
    "BINARY_XOR": operator.xor,
    "BINARY_OR": operator.or_,
}

JUMP_OPS = None

# --- exceptions ---


class VerifyCmpError(Exception):
    pass


class CmpErrorConsts(VerifyCmpError):
    """Exception to be raised when consts differ."""

    def __init__(self, name, index):
        self.name = name
        self.index = index

    def __str__(self):
        return "Compare Error within Consts of %s at index %i" % (
            repr(self.name),
            self.index,
        )


class CmpErrorConstsType(VerifyCmpError):
    """Exception to be raised when consts differ."""

    def __init__(self, name, index):
        self.name = name
        self.index = index

    def __str__(self):
        return "Consts type differ in %s at index %i" % (repr(self.name), self.index)


class CmpErrorConstsLen(VerifyCmpError):
    """Exception to be raised when length of co_consts differs."""

    def __init__(self, name, consts1, consts2):
        self.name = name
        self.consts = (consts1, consts2)

    def __str__(self):
        return "Consts length differs in %s:\n\n%i:\t%s\n\n%i:\t%s\n\n" % (
            repr(self.name),
            len(self.consts[0]),
            repr(self.consts[0]),
            len(self.consts[1]),
            repr(self.consts[1]),
        )


class CmpErrorCode(VerifyCmpError):
    """Exception to be raised when code differs."""

    def __init__(self, name, index, token1, token2, tokens1, tokens2):
        self.name = name
        self.index = index
        self.token1 = token1
        self.token2 = token2
        self.tokens = [tokens1, tokens2]

    def __str__(self):
        s = reduce(
            lambda s, t: "%s%-37s\t%-37s\n" % (s, t[0], t[1]),
            list(map(lambda a, b: (a, b), self.tokens[0], self.tokens[1])),
            "Code differs in %s\n" % str(self.name),
        )
        return (
            "Code differs in %s at offset %s [%s] != [%s]\n\n"
            % (repr(self.name), self.index, repr(self.token1), repr(self.token2))
        ) + s


class CmpErrorCodeLen(VerifyCmpError):
    """Exception to be raised when code length differs."""

    def __init__(self, name, tokens1, tokens2):
        self.name = name
        self.tokens = [tokens1, tokens2]

    def __str__(self):
        return reduce(
            lambda s, t: "%s%-37s\t%-37s\n" % (s, t[0], t[1]),
            list(map(lambda a, b: (a, b), self.tokens[0], self.tokens[1])),
            "Code len differs in %s\n" % str(self.name),
        )


class CmpErrorMember(VerifyCmpError):
    """Exception to be raised when other members differ."""

    def __init__(self, name, member, data1, data2):
        self.name = name
        self.member = member
        self.data = (data1, data2)

    def __str__(self):
        return "Member %s differs in %s:\n\t%s\n\t%s\n" % (
            repr(self.member),
            repr(self.name),
            repr(self.data[0]),
            repr(self.data[1]),
        )


# --- compare ---

# these members are ignored
__IGNORE_CODE_MEMBERS__ = [
    "co_filename",
    "co_firstlineno",
    "co_lnotab",
    "co_stacksize",
    "co_names",
]


def cmp_code_objects(version, is_pypy, code_obj1, code_obj2, verify, name=""):
    """
    Compare two code-objects.

    This is the main part of this module.
    """
    # print code_obj1, type(code_obj2)
    assert iscode(
        code_obj1
    ), "cmp_code_object first object type is %s, not code" % type(code_obj1)
    assert iscode(
        code_obj2
    ), "cmp_code_object second object type is %s, not code" % type(code_obj2)
    # print dir(code_obj1)
    if isinstance(code_obj1, object):
        # new style classes (Python 2.2)
        # assume _both_ code objects to be new stle classes
        assert dir(code_obj1) == dir(code_obj2)
    else:
        # old style classes
        assert dir(code_obj1) == code_obj1.__members__
        assert dir(code_obj2) == code_obj2.__members__
        assert code_obj1.__members__ == code_obj2.__members__

    if name == "__main__":
        name = code_obj1.co_name
    else:
        name = "%s.%s" % (name, code_obj1.co_name)
        if name == ".?":
            name = "__main__"

    if isinstance(code_obj1, object) and code_equal(code_obj1, code_obj2):
        # use the new style code-classes' __cmp__ method, which
        # should be faster and more sophisticated
        # if this compare fails, we use the old routine to
        # find out, what exactly is nor equal
        # if this compare succeds, simply return
        # return
        pass

    if isinstance(code_obj1, object):
        members = [x for x in dir(code_obj1) if x.startswith("co_")]
    else:
        members = dir(code_obj1)
    members.sort()  # ; members.reverse()

    tokens1 = None
    for member in members:
        if member in __IGNORE_CODE_MEMBERS__ or verify != "verify":
            pass
        elif member == "co_code":
            if verify != "strong":
                continue
            scanner = get_scanner(version, is_pypy, show_asm=False)

            global JUMP_OPS
            JUMP_OPS = list(JUMP_OPS) + ["JUMP_BACK"]

            # use changed Token class
            # We (re)set this here to save exception handling,
            # which would get confusing.
            scanner.setTokenClass(Token)
            try:
                # ingest both code-objects
                tokens1, customize = scanner.ingest(code_obj1)
                del customize  # save memory
                tokens2, customize = scanner.ingest(code_obj2)
                del customize  # save memory
            finally:
                scanner.resetTokenClass()  # restore Token class

            targets1 = dis.findlabels(code_obj1.co_code)
            tokens1 = [t for t in tokens1 if t.kind != "COME_FROM"]
            tokens2 = [t for t in tokens2 if t.kind != "COME_FROM"]

            i1 = 0
            i2 = 0
            offset_map = {}
            check_jumps = {}
            while i1 < len(tokens1):
                if i2 >= len(tokens2):
                    if (
                        len(tokens1) == len(tokens2) + 2
                        and tokens1[-1].kind == "RETURN_VALUE"
                        and tokens1[-2].kind == "LOAD_CONST"
                        and tokens1[-2].pattr is None
                        and tokens1[-3].kind == "RETURN_VALUE"
                    ):
                        break
                    else:
                        raise CmpErrorCodeLen(name, tokens1, tokens2)

                offset_map[tokens1[i1].offset] = tokens2[i2].offset

                for idx1, idx2, offset2 in check_jumps.get(tokens1[i1].offset, []):
                    if offset2 != tokens2[i2].offset:
                        raise CmpErrorCode(
                            name,
                            tokens1[idx1].offset,
                            tokens1[idx1],
                            tokens2[idx2],
                            tokens1,
                            tokens2,
                        )

                if tokens1[i1].kind != tokens2[i2].kind:
                    if tokens1[i1].kind == "LOAD_CONST" == tokens2[i2].kind:
                        i = 1
                        while tokens1[i1 + i].kind == "LOAD_CONST":
                            i += 1
                        if tokens1[i1 + i].kind.startswith(
                            ("BUILD_TUPLE", "BUILD_LIST")
                        ) and i == int(tokens1[i1 + i].kind.split("_")[-1]):
                            t = tuple([elem.pattr for elem in tokens1[i1 : i1 + i]])
                            if t != tokens2[i2].pattr:
                                raise CmpErrorCode(
                                    name,
                                    tokens1[i1].offset,
                                    tokens1[i1],
                                    tokens2[i2],
                                    tokens1,
                                    tokens2,
                                )
                            i1 += i + 1
                            i2 += 1
                            continue
                        elif (
                            i == 2
                            and tokens1[i1 + i].kind == "ROT_TWO"
                            and tokens2[i2 + 1].kind == "UNPACK_SEQUENCE_2"
                        ):
                            i1 += 3
                            i2 += 2
                            continue
                        elif i == 2 and tokens1[i1 + i].kind in BIN_OP_FUNCS:
                            f = BIN_OP_FUNCS[tokens1[i1 + i].kind]
                            if (
                                f(tokens1[i1].pattr, tokens1[i1 + 1].pattr)
                                == tokens2[i2].pattr
                            ):
                                i1 += 3
                                i2 += 1
                                continue
                    elif tokens1[i1].kind == "UNARY_NOT":
                        if tokens2[i2].kind == "POP_JUMP_IF_TRUE":
                            if tokens1[i1 + 1].kind == "POP_JUMP_IF_FALSE":
                                i1 += 2
                                i2 += 1
                                continue
                        elif tokens2[i2].kind == "POP_JUMP_IF_FALSE":
                            if tokens1[i1 + 1].kind == "POP_JUMP_IF_TRUE":
                                i1 += 2
                                i2 += 1
                                continue
                    elif (
                        tokens1[i1].kind in ("JUMP_FORWARD", "JUMP_BACK")
                        and tokens1[i1 - 1].kind == "RETURN_VALUE"
                        and tokens2[i2 - 1].kind in ("RETURN_VALUE", "RETURN_END_IF")
                        and int(tokens1[i1].offset) not in targets1
                    ):
                        i1 += 1
                        continue
                    elif (
                        tokens1[i1].kind == "JUMP_BACK"
                        and tokens2[i2].kind == "CONTINUE"
                    ):
                        # FIXME: should make sure that offset is inside loop, not outside of it
                        i1 += 2
                        i2 += 2
                        continue
                    elif (
                        tokens1[i1].kind == "JUMP_FORWARD"
                        and tokens2[i2].kind == "JUMP_BACK"
                        and tokens1[i1 + 1].kind == "JUMP_BACK"
                        and tokens2[i2 + 1].kind == "JUMP_BACK"
                        and int(tokens1[i1].pattr) == int(tokens1[i1].offset) + 3
                    ):
                        if int(tokens1[i1].pattr) == int(tokens1[i1 + 1].offset):
                            i1 += 2
                            i2 += 2
                            continue
                    elif (
                        tokens1[i1].kind == "LOAD_NAME"
                        and tokens2[i2].kind == "LOAD_CONST"
                        and tokens1[i1].pattr == "None"
                        and tokens2[i2].pattr is None
                    ):
                        pass
                    elif (
                        tokens1[i1].kind == "LOAD_GLOBAL"
                        and tokens2[i2].kind == "LOAD_NAME"
                        and tokens1[i1].pattr == tokens2[i2].pattr
                    ):
                        pass
                    elif (
                        tokens1[i1].kind == "LOAD_ASSERT"
                        and tokens2[i2].kind == "LOAD_NAME"
                        and tokens1[i1].pattr == tokens2[i2].pattr
                    ):
                        pass
                    elif (
                        tokens1[i1].kind == "RETURN_VALUE"
                        and tokens2[i2].kind == "RETURN_END_IF"
                    ):
                        pass
                    elif (
                        tokens1[i1].kind == "BUILD_TUPLE_0" and tokens2[i2].pattr == ()
                    ):
                        pass
                    else:
                        raise CmpErrorCode(
                            name,
                            tokens1[i1].offset,
                            tokens1[i1],
                            tokens2[i2],
                            tokens1,
                            tokens2,
                        )
                elif (
                    tokens1[i1].kind in JUMP_OPS
                    and tokens1[i1].pattr != tokens2[i2].pattr
                ):
                    if tokens1[i1].kind == "JUMP_BACK":
                        dest1 = int(tokens1[i1].pattr)
                        dest2 = int(tokens2[i2].pattr)
                        if offset_map[dest1] != dest2:
                            raise CmpErrorCode(
                                name,
                                tokens1[i1].offset,
                                tokens1[i1],
                                tokens2[i2],
                                tokens1,
                                tokens2,
                            )
                    else:
                        # import pdb; pdb.set_trace()
                        try:
                            dest1 = int(tokens1[i1].pattr)
                            if dest1 in check_jumps:
                                check_jumps[dest1].append((i1, i2, dest2))
                            else:
                                check_jumps[dest1] = [(i1, i2, dest2)]
                        except:
                            pass

                i1 += 1
                i2 += 1
            del tokens1, tokens2  # save memory
        elif member == "co_consts":
            # partial optimization can make the co_consts look different,
            #   so we'll just compare the code consts
            codes1 = (c for c in code_obj1.co_consts if hasattr(c, "co_consts"))
            codes2 = (c for c in code_obj2.co_consts if hasattr(c, "co_consts"))

            for c1, c2 in zip(codes1, codes2):
                cmp_code_objects(version, is_pypy, c1, c2, verify, name=name)
        elif member == "co_flags":
            flags1 = code_obj1.co_flags
            flags2 = code_obj2.co_flags
            if is_pypy:
                # For PYPY for now we don't care about PYPY_SOURCE_IS_UTF8:
                flags2 &= ~0x0100  # PYPY_SOURCE_IS_UTF8
            # We also don't care about COROUTINE or GENERATOR for now
            flags1 &= ~0x000000A0
            flags2 &= ~0x000000A0
            if flags1 != flags2:
                raise CmpErrorMember(
                    name,
                    "co_flags",
                    pretty_code_flags(flags1),
                    pretty_code_flags(flags2),
                )
        else:
            # all other members must be equal
            if getattr(code_obj1, member) != getattr(code_obj2, member):
                raise CmpErrorMember(
                    name, member, getattr(code_obj1, member), getattr(code_obj2, member)
                )


class Token(ScannerToken):
    """Token class with changed semantics for 'cmp()'."""

    def __cmp__(self, o):
        t = self.kind  # shortcut
        if t == "BUILD_TUPLE_0" and o.kind == "LOAD_CONST" and o.pattr == ():
            return 0
        if t == "COME_FROM" == o.kind:
            return 0
        if t == "PRINT_ITEM_CONT" and o.kind == "PRINT_ITEM":
            return 0
        if t == "RETURN_VALUE" and o.kind == "RETURN_END_IF":
            return 0
        if t == "JUMP_IF_FALSE_OR_POP" and o.kind == "POP_JUMP_IF_FALSE":
            return 0
        if JUMP_OPS and t in JUMP_OPS:
            # ignore offset
            return t == o.kind
        return (t == o.kind) or self.pattr == o.pattr

    def __repr__(self):
        return "%s %s (%s)" % (str(self.kind), str(self.attr), repr(self.pattr))

    def __str__(self):
        return "%s\t%-17s %r" % (self.offset, self.kind, self.pattr)


def compare_code_with_srcfile(pyc_filename, src_filename, verify):
    """Compare a .pyc with a source code file. If everything is okay, None
    is returned. Otherwise a string message describing the mismatch is returned.
    """
    (
        version,
        timestamp,
        magic_int,
        code_obj1,
        is_pypy,
        source_size,
        sip_hash,
    ) = load_module(pyc_filename)
    if magic_int != PYTHON_MAGIC_INT:
        msg = (
            "Can't compare code - Python is running with magic %s, but code is magic %s "
            % (PYTHON_MAGIC_INT, magic_int)
        )
        return msg
    try:
        code_obj2 = load_file(src_filename)
    except SyntaxError as e:
        # src_filename can be the first of a group sometimes
        return str(e).replace(src_filename, pyc_filename)
    cmp_code_objects(version, is_pypy, code_obj1, code_obj2, verify)
    if verify == "verify-run":
        try:
            retcode = call("%s %s" % (sys.executable, src_filename), shell=True)
            if retcode != 0:
                return "Child was terminated by signal %d" % retcode
            pass
        except OSError as e:
            return "Execution failed: %s" % e
        pass
    return None


def compare_files(pyc_filename1, pyc_filename2, verify):
    """Compare two .pyc files."""
    (
        version1,
        timestamp,
        magic_int1,
        code_obj1,
        is_pypy,
        source_size,
        sip_hash,
    ) = uncompyle6.load_module(pyc_filename1)
    (
        version2,
        timestamp,
        magic_int2,
        code_obj2,
        is_pypy,
        source_size,
        sip_hash,
    ) = uncompyle6.load_module(pyc_filename2)
    if (magic_int1 != magic_int2) and verify == "verify":
        verify = "weak_verify"
    cmp_code_objects(version1, is_pypy, code_obj1, code_obj2, verify)


if __name__ == "__main__":
    t1 = Token("LOAD_CONST", None, "code_object _expandLang", 52)
    t2 = Token("LOAD_CONST", -421, "code_object _expandLang", 55)
    print(repr(t1))
    print(repr(t2))
    print(t1.kind == t2.kind, t1.attr == t2.attr)
