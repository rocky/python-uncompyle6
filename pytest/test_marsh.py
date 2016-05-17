#!/usr/bin/env python

import os.path
from uncompyle6.load import load_module

def get_srcdir():
    filename = os.path.normcase(os.path.dirname(os.path.abspath(__file__)))
    return os.path.realpath(filename)

srcdir = get_srcdir()

def test_load_module():
    """Tests uncompile6.load.load_module"""
    # We deliberately pick a bytecode that we aren't likely to be running against
    mod_file = os.path.join(get_srcdir(), '..', 'test', 'bytecode_2.5',
                        '02_complex.pyc')

    version, timestamp, magic_int, co = load_module(mod_file)
    assert version == 2.5, "Should have picked up Python version properly"
    assert co.co_consts == (5j, None), "Code should have a complex constant"
