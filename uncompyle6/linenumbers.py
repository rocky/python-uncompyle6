from xdis.load import load_file, load_module
from xdis.bytecode import findlinestarts, offset2line

def line_number_mapping(pyc_filename, src_filename):
    (version, timestamp, magic_int, code_obj1, is_pypy,
     source_size) = load_module(pyc_filename)
    try:
        code_obj2 = load_file(src_filename)
    except SyntaxError as e:
        return str(e)

    linestarts_orig = findlinestarts(code_obj1)
    linestarts_uncompiled = list(findlinestarts(code_obj2))
    return [[line, offset2line(offset, linestarts_uncompiled)] for offset, line in linestarts_orig]
