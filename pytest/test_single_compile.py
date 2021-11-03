import pytest
from uncompyle6 import code_deparse
from xdis.version_info import PYTHON_VERSION_TRIPLE
pytestmark = pytest.mark.skip(PYTHON_VERSION_TRIPLE < (2, 7),
                              reason="need at least Python 2.7")

if PYTHON_VERSION_TRIPLE > (2, 6):
    def test_single_mode():
        single_expressions = (
            'i = 1',
            'i and (j or k)',
            'i += 1',
            'i = j % 4',
            'i = {}',
            'i = []',
            'for i in range(10):\n    i\n',
            'for i in range(10):\n    for j in range(10):\n        i + j\n',
            'try:\n    i\nexcept Exception:\n    j\nelse:\n    k\n'
        )

        for expr in single_expressions:
            code = compile(expr + '\n', '<string>', 'single')
            assert code_deparse(code, compile_mode='single').text == expr + '\n'
