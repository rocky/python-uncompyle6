import sys
from uncompyle6.load import load_file, check_object_path, load_module

def test_load():
    """Basic test of load_file, check_object_path and load_module"""
    co = load_file(__file__)
    obj_path = check_object_path(__file__)
    version, timestamp, magic_int, co2 = load_module(obj_path)
    assert sys.version[0:3] == str(version)
    assert co == co2
