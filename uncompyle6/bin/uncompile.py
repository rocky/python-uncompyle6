#!/usr/bin/env python
# Mode: -*- python -*-
#
# Copyright (c) 2015-2017, 2019-2020, 2023-2024
# by Rocky Bernstein
# Copyright (c) 2000-2002 by hartmut Goebel <h.goebel@crazy-compilers.com>
#
from __future__ import print_function

import os
import sys
import time
from typing import List

import click
from xdis.version_info import version_tuple_to_str

from uncompyle6.main import main, status_msg
from uncompyle6.verify import VerifyCmpError
from uncompyle6.version import __version__

program = "uncompyle6"


def usage():
    print(__doc__)
    sys.exit(1)


# __doc__ = """
# Usage:
#   %s [OPTIONS]... [ FILE | DIR]...
#   %s [--help | -h | --V | --version]

# Examples:
#   %s      foo.pyc bar.pyc       # decompile foo.pyc, bar.pyc to stdout
#   %s -o . foo.pyc bar.pyc       # decompile to ./foo.pyc_dis and ./bar.pyc_dis
#   %s -o /tmp /usr/lib/python1.5 # decompile whole library

# Options:
#   -o <path>     output decompiled files to this path:
#                 if multiple input files are decompiled, the common prefix
#                 is stripped from these names and the remainder appended to
#                 <path>
#                   uncompyle6 -o /tmp bla/fasel.pyc bla/foo.pyc
#                     -> /tmp/fasel.pyc_dis, /tmp/foo.pyc_dis
#                   uncompyle6 -o /tmp bla/fasel.pyc bar/foo.pyc
#                     -> /tmp/bla/fasel.pyc_dis, /tmp/bar/foo.pyc_dis
#                   uncompyle6 -o /tmp /usr/lib/python1.5
#                     -> /tmp/smtplib.pyc_dis ... /tmp/lib-tk/FixTk.pyc_dis
#   --compile | -c <python-file>
#                 attempts a decompilation after compiling <python-file>
#   -d            print timestamps
#   -p <integer>  use <integer> number of processes
#   -r            recurse directories looking for .pyc and .pyo files
#   --fragments   use fragments deparser
#   --verify      compare generated source with input byte-code
#   --verify-run  compile generated source, run it and check exit code
#   --syntax-verify compile generated source
#   --linemaps    generated line number correspondencies between byte-code
#                 and generated source output
#   --encoding  <encoding>
#                 use <encoding> in generated source according to pep-0263
#   --help        show this message

# Debugging Options:
#   --asm     | -a        include byte-code       (disables --verify)
#   --grammar | -g        show matching grammar
#   --tree={before|after}
#   -t {before|after}     include syntax before (or after) tree transformation
#                         (disables --verify)
#   --tree++ | -T         add template rules to --tree=before when possible

# Extensions of generated files:
#   '.pyc_dis' '.pyo_dis'   successfully decompiled (and verified if --verify)
#     + '_unverified'       successfully decompile but --verify failed
#     + '_failed'           decompile failed (contact author for enhancement)
# """ % (
#     (program,) * 5
# )


@click.command()
@click.option(
    "--asm++/--no-asm++",
    "-A",
    "asm_plus",
    default=False,
    help="show xdis assembler and tokenized assembler",
)
@click.option("--asm/--no-asm", "-a", default=False)
@click.option("--grammar/--no-grammar", "-g", "show_grammar", default=False)
@click.option("--tree/--no-tree", "-t", default=False)
@click.option(
    "--tree++/--no-tree++",
    "-T",
    "tree_plus",
    default=False,
    help="show parse tree and Abstract Syntax Tree",
)
@click.option(
    "--linemaps/--no-linemaps",
    default=False,
    help="show line number correspondencies between byte-code "
    "and generated source output",
)
@click.option(
    "--verify",
    type=click.Choice(["run", "syntax"]),
    default=None,
)
@click.option(
    "--recurse/--no-recurse",
    "-r",
    "recurse_dirs",
    default=False,
)
@click.option(
    "--output",
    "-o",
    "outfile",
    type=click.Path(
        exists=True, file_okay=True, dir_okay=True, writable=True, resolve_path=True
    ),
    required=False,
)
@click.version_option(version=__version__)
@click.option(
    "--start-offset",
    "start_offset",
    default=0,
    help="start decomplation at offset; default is 0 or the starting offset.",
)
@click.version_option(version=__version__)
@click.option(
    "--stop-offset",
    "stop_offset",
    default=-1,
    help="stop decomplation when seeing an offset greater or equal to this; default is "
    "-1 which indicates no stopping point.",
)
@click.argument("files", nargs=-1, type=click.Path(readable=True), required=True)
def main_bin(
    asm: bool,
    asm_plus: bool,
    show_grammar,
    tree: bool,
    tree_plus: bool,
    linemaps: bool,
    verify,
    recurse_dirs: bool,
    outfile,
    start_offset: int,
    stop_offset: int,
    files,
):
    """
    Cross Python bytecode decompiler for Python bytecode up to Python 3.8.
    """

    version_tuple = sys.version_info[0:2]
    if version_tuple < (3, 6):
        print(
            f"Error: This version of the {program} runs from Python 3.6 or greater."
            f"You need another branch of this code for Python before 3.6."
            f""" \n\tYou have version: {version_tuple_to_str()}."""
        )
        sys.exit(-1)

    numproc = 0
    out_base = None

    out_base = None
    source_paths: List[str] = []
    timestamp = False
    timestampfmt = "# %Y.%m.%d %H:%M:%S %Z"
    pyc_paths = files

    # Expand directory if "recurse" was specified.
    if recurse_dirs:
        expanded_files = []
        for f in pyc_paths:
            if os.path.isdir(f):
                for root, _, dir_files in os.walk(f):
                    for df in dir_files:
                        if df.endswith(".pyc") or df.endswith(".pyo"):
                            expanded_files.append(os.path.join(root, df))
        pyc_paths = expanded_files

    # argl, commonprefix works on strings, not on path parts,
    # thus we must handle the case with files in 'some/classes'
    # and 'some/cmds'
    src_base = os.path.commonprefix(pyc_paths)
    if src_base[-1:] != os.sep:
        src_base = os.path.dirname(src_base)
    if src_base:
        sb_len = len(os.path.join(src_base, ""))
        pyc_paths = [f[sb_len:] for f in pyc_paths]

    if not pyc_paths and not source_paths:
        print("No input files given to decompile", file=sys.stderr)
        usage()

    if outfile == "-":
        outfile = None  # use stdout
    elif outfile and os.path.isdir(outfile):
        out_base = outfile
        outfile = None
    elif outfile and len(pyc_paths) > 1:
        out_base = outfile
        outfile = None

    # A second -a turns show_asm="after" into show_asm="before"
    if asm_plus or asm:
        asm_opt = "both" if asm_plus else "after"
    else:
        asm_opt = None

    if timestamp:
        print(time.strftime(timestampfmt))

    if numproc <= 1:
        show_ast = {"before": tree or tree_plus, "after": tree_plus}
        try:
            result = main(
                src_base,
                out_base,
                pyc_paths,
                source_paths,
                outfile,
                showasm=asm_opt,
                showgrammar=show_grammar,
                showast=show_ast,
                do_verify=verify,
                do_linemaps=linemaps,
                start_offset=start_offset,
                stop_offset=stop_offset,
            )
            if len(pyc_paths) > 1:
                mess = status_msg(*result)
                print("# " + mess)
                pass
        except ImportError as e:
            print(str(e))
            sys.exit(2)
        except KeyboardInterrupt:
            pass
        except VerifyCmpError:
            raise
    else:
        from multiprocessing import Process, Queue

        try:
            from Queue import Empty
        except ImportError:
            from queue import Empty

        fqueue = Queue(len(pyc_paths) + numproc)
        for f in pyc_paths:
            fqueue.put(f)
        for i in range(numproc):
            fqueue.put(None)

        rqueue = Queue(numproc)

        tot_files = okay_files = failed_files = verify_failed_files = 0

        def process_func():
            (tot_files, okay_files, failed_files, verify_failed_files) = (
                0,
                0,
                0,
                0,
            )
            try:
                while 1:
                    f = fqueue.get()
                    if f is None:
                        break
                    (t, o, f, v) = main(src_base, out_base, [f], [], outfile)
                    tot_files += t
                    okay_files += o
                    failed_files += f
                    verify_failed_files += v
            except (Empty, KeyboardInterrupt):
                pass
            rqueue.put((tot_files, okay_files, failed_files, verify_failed_files))
            rqueue.close()

        try:
            procs = [Process(target=process_func) for i in range(numproc)]
            for p in procs:
                p.start()
            for p in procs:
                p.join()
            try:
                (tot_files, okay_files, failed_files, verify_failed_files) = (
                    0,
                    0,
                    0,
                    0,
                )
                while True:
                    (t, o, f, v) = rqueue.get(False)
                    tot_files += t
                    okay_files += o
                    failed_files += f
                    verify_failed_files += v
            except Empty:
                pass
            print(
                "# decompiled %i files: %i okay, %i failed, %i verify failed"
                % (tot_files, okay_files, failed_files, verify_failed_files)
            )
        except (KeyboardInterrupt, OSError):
            pass

    if timestamp:
        print(time.strftime(timestampfmt))

    return


if __name__ == "__main__":
    main_bin()
