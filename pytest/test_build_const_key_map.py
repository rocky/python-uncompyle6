import pytest
# uncompyle6
from xdis.version_info import PYTHON_VERSION_TRIPLE, IS_PYPY
from validate import validate_uncompyle


@pytest.mark.skipif(PYTHON_VERSION_TRIPLE < (3, 6) or IS_PYPY, reason="need at least Python 3.6 and not PyPY")
@pytest.mark.parametrize('text', (
    "{0.: 'a', -1: 'b'}",   # BUILD_MAP
    "{'a':'b'}",            # BUILD_MAP
    "{0: 1}",               # BUILD_MAP
    "{b'0':1, b'2':3}",     # BUILD_CONST_KEY_MAP
    "{0: 1, 2: 3}",         # BUILD_CONST_KEY_MAP
    "{'a':'b','c':'d'}",    # BUILD_CONST_KEY_MAP
    "{0: 1, 2: 3}",         # BUILD_CONST_KEY_MAP
    "{'a': 1, 'b': 2}",     # BUILD_CONST_KEY_MAP
    "{'a':'b','c':'d'}",    # BUILD_CONST_KEY_MAP
    "{0.0:'b',0.1:'d'}",    # BUILD_CONST_KEY_MAP
))
def test_build_const_key_map(text):
    validate_uncompyle(text)
