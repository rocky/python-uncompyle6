#!/usr/bin/env python
from uncompyle6 import PYTHON_VERSION
from uncompyle6.scanner import get_scanner
from array import array
def bug(state, slotstate):
    if state:
        if slotstate is not None:
            for key, value in slotstate.items():
                setattr(state, key, 2)

def test_if_in_for():
    code = bug.__code__
    scan = get_scanner(PYTHON_VERSION)
    print(PYTHON_VERSION)
    if 2.7 <= PYTHON_VERSION <= 3.0:
        n = scan.setup_code(code)
        scan.build_lines_data(code, n)
        scan.build_prev_op(n)
        fjt = scan.find_jump_targets()
        assert {15: [3], 69: [66], 63: [18]} == fjt
        print(scan.structs)
        assert scan.structs == \
          [{'start': 0, 'end': 72, 'type': 'root'},
           {'start': 18, 'end': 66, 'type': 'if-then'},
           {'start': 31, 'end': 59, 'type': 'for-loop'},
           {'start': 62, 'end': 63, 'type': 'for-else'}]
    elif 3.2 < PYTHON_VERSION <= 3.4:
        scan.code = array('B', code.co_code)
        scan.build_lines_data(code)
        scan.build_prev_op()
        fjt  = scan.find_jump_targets()
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
