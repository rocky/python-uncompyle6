#  Copyright (c) 2018, 2022-2024 by Rocky Bernstein
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

import sys

from spark_parser import DEFAULT_DEBUG as PARSER_DEFAULT_DEBUG
from xdis import iscode

from xdis.version_info import IS_PYPY, PYTHON_VERSION_TRIPLE

from uncompyle6.scanner import get_scanner
from uncompyle6.semantics.consts import  ASSIGN_DOC_STRING

from uncompyle6.semantics.pysource import (
    RETURN_NONE,
    TREE_DEFAULT_DEBUG,
    SourceWalker,
    SourceWalkerError,
    find_globals_and_nonlocals
)
from uncompyle6.show import maybe_show_asm

#


class AligningWalker(SourceWalker, object):
    def __init__(
        self,
        version,
        out,
        scanner,
        showast=TREE_DEFAULT_DEBUG,
        debug_parser=PARSER_DEFAULT_DEBUG,
        compile_mode="exec",
        is_pypy=False,
    ):
        SourceWalker.__init__(
            self, version, out, scanner, showast, debug_parser, compile_mode, is_pypy
        )
        self.desired_line_number = 0
        self.current_line_number = 0
        self.showast = showast

    def println(self, *data):
        if data and not (len(data) == 1 and data[0] == ""):
            self.write(*data)

        self.pending_newlines = max(self.pending_newlines, 1)

    def write(self, *data):
        if (len(data) == 1) and data[0] == self.indent:
            diff = max(
                self.pending_newlines,
                self.desired_line_number - self.current_line_number,
            )
            self.f.write("\n" * diff)
            self.current_line_number += diff
            self.pending_newlines = 0
        if (len(data) == 0) or (len(data) == 1 and data[0] == ""):
            return

        out = "".join((str(j) for j in data))
        n = 0
        for i in out:
            if i == "\n":
                n += 1
                if n == len(out):
                    self.pending_newlines = max(self.pending_newlines, n)
                    return
            elif n:
                self.pending_newlines = max(self.pending_newlines, n)
                out = out[n:]
                break
            else:
                break

        if self.pending_newlines > 0:
            diff = max(
                self.pending_newlines,
                self.desired_line_number - self.current_line_number,
            )
            self.f.write("\n" * diff)
            self.current_line_number += diff
            self.pending_newlines = 0

        for i in out[::-1]:
            if i == "\n":
                self.pending_newlines += 1
            else:
                break

        if self.pending_newlines:
            out = out[: -self.pending_newlines]
        self.f.write(out)

    def default(self, node):
        mapping = self._get_mapping(node)
        if hasattr(node, "linestart"):
            if node.linestart:
                self.desired_line_number = node.linestart
        table = mapping[0]
        key = node

        for i in mapping[1:]:
            key = key[i]
            pass

        if key.kind in table:
            self.template_engine(table[key.kind], node)
            self.prune()


DEFAULT_DEBUG_OPTS = {"asm": False, "tree": TREE_DEFAULT_DEBUG, "grammar": False}


def code_deparse_align(
    co,
    out=sys.stderr,
    version=None,
    is_pypy=None,
    debug_opts=DEFAULT_DEBUG_OPTS,
    code_objects={},
    compile_mode="exec",
):
    """
    ingests and deparses a given code block 'co'
    """

    assert iscode(co)

    if version is None:
        version = PYTHON_VERSION_TRIPLE
    if is_pypy is None:
        is_pypy = IS_PYPY

    # store final output stream for case of error
    scanner = get_scanner(version, is_pypy=is_pypy)

    tokens, customize = scanner.ingest(co, code_objects=code_objects)
    show_asm = debug_opts.get("asm", None)
    maybe_show_asm(show_asm, tokens)

    debug_parser = dict(PARSER_DEFAULT_DEBUG)
    show_grammar = debug_opts.get("grammar", None)
    show_grammar = debug_opts.get("grammar", None)
    if show_grammar:
        debug_parser["reduce"] = show_grammar
        debug_parser["errorstack"] = True

    #  Build a parse tree from tokenized and massaged disassembly.
    show_ast = debug_opts.get("ast", TREE_DEFAULT_DEBUG)
    deparsed = AligningWalker(
        version,
        out,
        scanner,
        showast=show_ast,
        debug_parser=debug_parser,
        compile_mode=compile_mode,
        is_pypy=is_pypy,
    )

    is_top_level_module = co.co_name == "<module>"
    deparsed.ast = deparsed.build_ast(
        tokens, customize, co, is_top_level_module=is_top_level_module
    )

    assert deparsed.ast == "stmts", "Should have parsed grammar start"

    del tokens  # save memory

    (deparsed.mod_globs, _) = find_globals_and_nonlocals(
        deparsed.ast, set(), set(), co, version
    )

    # convert leading '__doc__ = "..." into doc string
    try:
        if deparsed.ast[0][0] == ASSIGN_DOC_STRING(co.co_consts[0]):
            deparsed.print_docstring("", co.co_consts[0])
            del deparsed.ast[0]
        if deparsed.ast[-1] == RETURN_NONE:
            deparsed.ast.pop()  # remove last node
            # todo: if empty, add 'pass'
    except Exception:
        pass

    # What we've been waiting for: Generate Python source from the parse tree!
    deparsed.gen_source(deparsed.ast, co.co_name, customize)

    for g in sorted(deparsed.mod_globs):
        deparsed.write("# global %s ## Warning: Unused global\n" % g)

    if deparsed.ERROR:
        raise SourceWalkerError("Deparsing stopped due to parse error")
    return deparsed


if __name__ == "__main__":

    def deparse_test(co):
        "This is a docstring"
        deparsed = code_deparse_align(co)
        print(deparsed.text)
        return

    deparse_test(deparse_test.func_code)
