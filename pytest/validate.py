# future
from __future__ import print_function
# std
import os
import difflib
import subprocess
import tempfile
import functools
# compatability
import six
# uncompyle6 / xdis
from uncompyle6 import PYTHON_VERSION, IS_PYPY, deparse_code
# TODO : I think we can get xdis to support the dis api (python 3 version) by doing something like this there
from xdis.bytecode import Bytecode
from xdis.main import get_opcode
opc = get_opcode(PYTHON_VERSION, IS_PYPY)
Bytecode = functools.partial(Bytecode, opc=opc)


def _dis_to_text(co):
    return Bytecode(co).dis()


def print_diff(original, uncompyled):
    """
    Try and display a pretty html line difference between the original and
    uncompyled code and bytecode if elinks and BeautifulSoup are installed
    otherwise just show the diff.

    :param original: Text describing the original code object.
    :param uncompyled: Text describing the uncompyled code object.
    """
    original_lines = original.split('\n')
    uncompyled_lines = uncompyled.split('\n')
    args = original_lines, uncompyled_lines, 'original', 'uncompyled'
    try:
        from bs4 import BeautifulSoup
        diff = difflib.HtmlDiff().make_file(*args)
        diff = BeautifulSoup(diff, "html.parser")
        diff.select_one('table[summary="Legends"]').extract()
    except ImportError:
        print('\nTo display diff highlighting run:\n    pip install BeautifulSoup4')
        diff = difflib.HtmlDiff().make_table(*args)

    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(str(diff).encode('utf-8'))

    try:
        print()
        html = subprocess.check_output([
            'elinks',
            '-dump',
            '-no-references',
            '-dump-color-mode',
            '1',
            f.name,
        ]).decode('utf-8')
        print(html)
    except:
        print('\nFor side by side diff install elinks')
        diff = difflib.Differ().compare(original_lines, uncompyled_lines)
        print('\n'.join(diff))
    finally:
        os.unlink(f.name)


def are_instructions_equal(i1, i2):
    """
    Determine if two instructions are approximately equal,
    ignoring certain fields which we allow to differ, namely:

    * code objects are ignore (should probaby be checked) due to address
    * line numbers

    :param i1: left instruction to compare
    :param i2: right instruction to compare

    :return: True if the two instructions are approximately equal, otherwise False.
    """
    result = (1==1
        and i1.opname == i2.opname
        and i1.opcode == i2.opcode
        and i1.arg == i2.arg
        # ignore differences due to code objects
        # TODO : Better way of ignoring address
        and (i1.argval == i2.argval or '<code object' in str(i1.argval))
        # TODO : Should probably recurse to check code objects
        and (i1.argrepr == i2.argrepr or '<code object' in i1.argrepr)
        and i1.offset == i2.offset
        # ignore differences in line numbers
        #and i1.starts_line
        and i1.is_jump_target == i2.is_jump_target
    )
    return result


def are_code_objects_equal(co1, co2):
    """
    Determine if two code objects are approximately equal,
    see are_instructions_equal for more information.

    :param i1: left code object to compare
    :param i2: right code object to compare

    :return: True if the two code objects are approximately equal, otherwise False.
    """
    instructions1 = Bytecode(co1)
    instructions2 = Bytecode(co2)
    for opcode1, opcode2 in zip(instructions1, instructions2):
        if not are_instructions_equal(opcode1, opcode2):
            return False
    return True


def validate_uncompyle(text, mode='exec'):
    """
    Validate decompilation of the given source code.

    :param text: Source to validate decompilation of.
    """
    original_code = compile(text, '<string>', mode)
    original_dis = _dis_to_text(original_code)
    original_text = text

    deparsed = deparse_code(PYTHON_VERSION, original_code,
                            compile_mode=mode,
                            out=six.StringIO(),
                            is_pypy=IS_PYPY)
    uncompyled_text = deparsed.text
    uncompyled_code = compile(uncompyled_text, '<string>', 'exec')

    if not are_code_objects_equal(uncompyled_code, original_code):

        uncompyled_dis = _dis_to_text(uncompyled_text)

        def output(text, dis):
            width = 60
            return '\n\n'.join([
                ' SOURCE CODE '.center(width, '#'),
                text.strip(),
                ' BYTECODE '.center(width, '#'),
                dis
            ])

        original = output(original_text, original_dis)
        uncompyled = output(uncompyled_text, uncompyled_dis)
        print_diff(original, uncompyled)

        assert 'original' == 'uncompyled'
