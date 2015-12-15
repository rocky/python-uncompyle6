import os.path
import pytest

from uncompyle6.disas import disassemble_file

def get_srcdir():
    filename = os.path.normcase(os.path.dirname(__file__))
    return os.path.realpath(filename)

src_dir = get_srcdir()
os.chdir(src_dir)


@pytest.mark.parametrize(("test_tuple", "function_to_test"), [
    (
        ('../test/bytecode_2.5/test_import.pyc', 'testdata/test_import_25.right',),
        disassemble_file
    ),
    (
        ('../test/bytecode_2.7/test1.pyc', 'testdata/test1.right',),
        disassemble_file
    ),
])
def test_funcoutput(capfd, test_tuple, function_to_test):

    in_file , filename_expected = test_tuple
    function_to_test(in_file)
    resout, reserr = capfd.readouterr()
    expected = open(filename_expected, "r").read()
    if resout != expected:
        with open(filename_expected + ".got", "w") as out:
            out.write(resout)
    assert resout == expected
