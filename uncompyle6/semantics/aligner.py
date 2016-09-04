import sys
from uncompyle6.semantics.pysource import (
    SourceWalker, SourceWalkerError, find_globals, ASSIGN_DOC_STRING, RETURN_NONE)
from spark_parser import DEFAULT_DEBUG as PARSER_DEFAULT_DEBUG
class AligningWalker(SourceWalker, object):
    def __init__(self, version, scanner, out, showast=False,
                 debug_parser=PARSER_DEFAULT_DEBUG,
                 compile_mode='exec', is_pypy=False):
        SourceWalker.__init__(self, version, out, scanner, showast, debug_parser,
                              compile_mode, is_pypy)
        self.desired_line_number = 0
        self.current_line_number = 0

    def println(self, *data):
        if data and not(len(data) == 1 and data[0] ==''):
            self.write(*data)

        self.pending_newlines = max(self.pending_newlines, 1)

    def write(self, *data):
        from trepan.api import debug; debug()
        if (len(data) == 1) and data[0] == self.indent:
            diff = max(self.pending_newlines,
                       self.desired_line_number - self.current_line_number)
            self.f.write('\n'*diff)
            self.current_line_number += diff
            self.pending_newlines = 0
        if (len(data) == 0) or (len(data) == 1 and data[0] == ''):
            return

        out = ''.join((str(j) for j in data))
        n = 0
        for i in out:
            if i == '\n':
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
            diff = max(self.pending_newlines,
                       self.desired_line_number - self.current_line_number)
            self.f.write('\n'*diff)
            self.current_line_number += diff
            self.pending_newlines = 0

        for i in out[::-1]:
            if i == '\n':
                self.pending_newlines += 1
            else:
                break

        if self.pending_newlines:
            out = out[:-self.pending_newlines]
        self.f.write(out)

    def default(self, node):
        mapping = self._get_mapping(node)
        if hasattr(node, 'linestart'):
            if node.linestart:
                self.desired_line_number = node.linestart
        table = mapping[0]
        key = node

        for i in mapping[1:]:
            key = key[i]
            pass

        if key.type in table:
            self.engine(table[key.type], node)
            self.prune()

from xdis.code import iscode
from uncompyle6.scanner import get_scanner
from uncompyle6.show import (
    maybe_show_asm,
)

def align_deparse_code(version, co, out=sys.stderr, showasm=False, showast=False,
                 showgrammar=False, code_objects={}, compile_mode='exec', is_pypy=False):
    """
    ingests and deparses a given code block 'co'
    """

    assert iscode(co)
    # store final output stream for case of error
    scanner = get_scanner(version, is_pypy=is_pypy)

    tokens, customize = scanner.ingest(co, code_objects=code_objects)
    maybe_show_asm(showasm, tokens)

    debug_parser = dict(PARSER_DEFAULT_DEBUG)
    if showgrammar:
        debug_parser['reduce'] = showgrammar
        debug_parser['errorstack'] = True

    #  Build AST from disassembly.
    deparsed = AligningWalker(version, scanner, out, showast=showast,
                            debug_parser=debug_parser, compile_mode=compile_mode,
                            is_pypy = is_pypy)

    isTopLevel = co.co_name == '<module>'
    deparsed.ast = deparsed.build_ast(tokens, customize, isTopLevel=isTopLevel)

    assert deparsed.ast == 'stmts', 'Should have parsed grammar start'

    del tokens # save memory

    deparsed.mod_globs = find_globals(deparsed.ast, set())

    # convert leading '__doc__ = "..." into doc string
    try:
        if deparsed.ast[0][0] == ASSIGN_DOC_STRING(co.co_consts[0]):
            deparsed.print_docstring('', co.co_consts[0])
            del deparsed.ast[0]
        if deparsed.ast[-1] == RETURN_NONE:
            deparsed.ast.pop() # remove last node
            # todo: if empty, add 'pass'
    except:
        pass

    # What we've been waiting for: Generate source from AST!
    deparsed.gen_source(deparsed.ast, co.co_name, customize)

    for g in deparsed.mod_globs:
        deparsed.write('# global %s ## Warning: Unused global' % g)

    if deparsed.ERROR:
        raise SourceWalkerError("Deparsing stopped due to parse error")
    return deparsed

if __name__ == '__main__':
    def deparse_test(co):
        "This is a docstring"
        sys_version = sys.version_info.major + (sys.version_info.minor / 10.0)
        # deparsed = deparse_code(sys_version, co, showasm=True, showast=True)
        deparsed = align_deparse_code(sys_version, co, showasm=False, showast=False,
                                      showgrammar=False)
        print(deparsed.text)
        return
    deparse_test(deparse_test.__code__)
