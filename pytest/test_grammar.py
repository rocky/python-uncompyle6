import pytest
from uncompyle6 import PYTHON_VERSION, PYTHON3 # , PYTHON_VERSION
from uncompyle6.parser import get_python_parser

def test_grammar():
    p = get_python_parser(PYTHON_VERSION)
    lhs, rhs, tokens, right_recursive = p.checkSets()
    expect_lhs = set(['expr1024', 'pos_arg'])
    unused_rhs = set(['build_list', 'call_function', 'mkfunc', 'mklambda',
                      'unpack', 'unpack_list'])
    expect_right_recursive = [['designList', ('designator', 'DUP_TOP', 'designList')]]
    if PYTHON3:
        expect_lhs.add('load_genexpr')
        unused_rhs = unused_rhs.union(set("""
        except_pop_except genexpr classdefdeco2 listcomp
        """.split()))
    else:
        expect_lhs.add('kwarg')
    assert expect_lhs == set(lhs)
    assert unused_rhs == set(rhs)
    assert expect_right_recursive == right_recursive
    # FIXME: check that tokens are in list of opcodes
    # print(tokens)
