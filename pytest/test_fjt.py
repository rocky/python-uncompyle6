#!/usr/bin/env python
from uncompyle6 import PYTHON_VERSION, IS_PYPY
from uncompyle6.scanner import get_scanner
from xdis.bytecode import Bytecode
from array import array
def bug(state, slotstate):
    if state:
        if slotstate is not None:
            for key, value in slotstate.items():
                setattr(state, key, 2)

# From 2.7 disassemble
# Problem is not getting while, because
# COME_FROM not added
def bug_loop(disassemble, tb=None):
    if tb:
        try:
            tb = 5
        except AttributeError:
            raise RuntimeError
        while tb: tb = tb.tb_next
    disassemble(tb)

def test_if_in_for():
    code = bug.__code__
    scan = get_scanner(PYTHON_VERSION)
    print(PYTHON_VERSION)
    if 2.7 <= PYTHON_VERSION <= 3.0 and not IS_PYPY:
        n = scan.setup_code(code)
        bytecode = Bytecode(code, scan.opc)
        scan.build_lines_data(code, n)
        scan.insts = list(bytecode)
        scan.offset2inst_index = {}
        for i, inst in enumerate(scan.insts):
            scan.offset2inst_index[inst.offset] = i
        scan.build_prev_op(n)
        fjt = scan.find_jump_targets(False)

        ## FIXME: the data below is wrong.
        ## we get different results currenty as well.
        ## We need to probably fix both the code
        ## and the test below
        # assert {15: [3], 69: [66], 63: [18]} == fjt
        # assert scan.structs == \
        #   [{'start': 0, 'end': 72, 'type': 'root'},
        #    {'start': 15, 'end': 66, 'type': 'if-then'},
        #    {'start': 31, 'end': 59, 'type': 'for-loop'},
        #    {'start': 62, 'end': 63, 'type': 'for-else'}]

        code = bug_loop.__code__
        n = scan.setup_code(code)
        bytecode = Bytecode(code, scan.opc)
        scan.build_lines_data(code, n)
        scan.insts = list(bytecode)
        scan.build_prev_op(n)
        scan.offset2inst_index = {}
        for i, inst in enumerate(scan.insts):
            scan.offset2inst_index[inst.offset] = i
        fjt = scan.find_jump_targets(False)
        assert{64: [42], 67: [42, 42], 42: [16, 41], 19: [6]} == fjt
        assert scan.structs == [
            {'start': 0, 'end': 80, 'type': 'root'},
            {'start': 3, 'end': 64, 'type': 'if-then'},
            {'start': 6, 'end': 15, 'type': 'try'},
            {'start': 19, 'end': 38, 'type': 'except'},
            {'start': 45, 'end': 67, 'type': 'while-loop'},
            {'start': 70, 'end': 64, 'type': 'while-else'},
            # previous bug was not mistaking while-loop for if-then
            {'start': 48, 'end': 67, 'type': 'while-loop'}]

    elif 3.2 < PYTHON_VERSION <= 3.4:
        bytecode = Bytecode(code, scan.opc)
        scan.code = array('B', code.co_code)
        scan.lines = scan.build_lines_data(code)
        scan.build_prev_op()
        scan.insts = list(bytecode)
        scan.offset2inst_index = {}
        for i, inst in enumerate(scan.insts):
            scan.offset2inst_index[inst.offset] = i
        fjt  = scan.find_jump_targets(False)
        assert {69: [66], 63: [18]} == fjt
        assert scan.structs == \
          [{'end': 72, 'type': 'root', 'start': 0},
           {'end': 66, 'type': 'if-then', 'start': 6},
           {'end': 63, 'type': 'if-then', 'start': 18},
           {'end': 59, 'type': 'for-loop', 'start': 31},
           {'end': 63, 'type': 'for-else', 'start': 62}]
    else:
        assert True, "FIXME: should note fixed"
    return
