import pytest
# uncompyle6
from uncompyle6 import PYTHON_VERSION
from validate import validate_uncompyle


@pytest.mark.skipif(PYTHON_VERSION < 3.6, reason='need at least python 3.6')
@pytest.mark.parametrize('text', (
    "{-0.: 'a', -1: 'b'}",
    "{0.: 'a', -1: 'b'}",
    "{0: 1, 2: 3}",
    "{-0: 1, 2: 3}",
))
def test_build_const_key_map(text):
    validate_uncompyle(text)
