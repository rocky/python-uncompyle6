import pytest
from uncompyle6 import PYTHON_VERSION, PYTHON3, deparse_code

def test_single_mode():
    single_expressions = (
        'i = 1',
        'i and (j or k)',
        'i += 1',
        'i = j % 4',
        'i = {}',
        'i = []',
        'while i < 1 or stop:\n    i\n',
        'while i < 1 or stop:\n    print%s\n' % ('(i)' if PYTHON3 else ' i'),
        'for i in range(10):\n    i\n',
        'for i in range(10):\n    for j in range(10):\n        i + j\n',
        'try:\n    i\nexcept Exception:\n    j\nelse:\n    k\n'
    )

    for expr in single_expressions:
        code = compile(expr + '\n', '<string>', 'single')
        assert deparse_code(PYTHON_VERSION, code, compile_mode='single').text == expr + '\n'
