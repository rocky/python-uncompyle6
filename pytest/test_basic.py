from uncompyle6.scanner import get_scanner
from uncompyle6.parser import get_python_parser

def test_get_scanner():
    # See that we can retrieve a scanner using a full version number
    assert get_scanner('2.7.13')


def test_get_parser():
    # See that we can retrieve a sparser using a full version number
    assert get_python_parser('2.7.13')
