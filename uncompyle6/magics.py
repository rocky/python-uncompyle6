from __future__ import print_function

import imp, struct, sys

def __build_magic(magic):
    if (sys.version_info >= (3, 0)):
        return struct.pack('Hcc', magic, bytes('\r', 'utf-8'), bytes('\n', 'utf-8'))
    else:
        return struct.pack('Hcc', magic, '\r', '\n')

def magic2int(magic):
    return struct.unpack('Hcc', magic)[0]

PYTHON_MAGIC_INT = magic2int(imp.get_magic())

by_magic = {}
by_version = {}

def __by_version(magics):
    for m, v in list(magics.items()):
        by_magic[m] = v
        by_version[v] = m
    return by_version

versions = {
    # taken from from Python/import.c
    # or importlib/_bootstrap.py
    # magic, version
    __build_magic(20121): '1.5', # 1.5, 1.5.1, 1.5.2
    __build_magic(50428): '1.6', # 1.6
    __build_magic(50823): '2.0', # 2.0, 2.0.1
    __build_magic(60202): '2.1', # 2.1, 2.1.1, 2.1.2
    __build_magic(60717): '2.2', # 2.2
    __build_magic(62011): '2.3', # 2.3a0
    __build_magic(62021): '2.3', # 2.3a0
    __build_magic(62041): '2.4', # 2.4a0
    __build_magic(62051): '2.4', # 2.4a3
    __build_magic(62061): '2.4', # 2.4b1
    __build_magic(62071): '2.5', # 2.5a0
    __build_magic(62081): '2.5', # 2.5a0 (ast-branch)
    __build_magic(62091): '2.5', # 2.5a0 (with)
    __build_magic(62092): '2.5', # 2.5a0 (changed WITH_CLEANUP opcode)
    __build_magic(62101): '2.5', # 2.5b3 (fix wrong code: for x, in ...)
    __build_magic(62111): '2.5', # 2.5b3 (fix wrong code: x += yield)
    __build_magic(62121): '2.5', # 2.5c1 (fix wrong lnotab with for loops and
                                 #  storing constants that should have been removed
    __build_magic(62131): '2.5', # 2.5c2 (fix wrong code: for x, in ... in listcomp/genexp)
    __build_magic(62151): '2.6', # 2.6a0 (peephole optimizations & STORE_MAP)
    __build_magic(62161): '2.6', # 2.6a1 (WITH_CLEANUP optimization)
    __build_magic(62171): '2.7', # 2.7a0 (optimize list comprehensions/change LIST_APPEND)
    __build_magic(62181): '2.7', # 2.7a0 (optimize conditional branches:
                                 #  introduce POP_JUMP_IF_FALSE and POP_JUMP_IF_TRUE)
    __build_magic(62191): '2.7', # 2.7a0 (introduce SETUP_WITH)
    __build_magic(62201): '2.7', # 2.7a0 (introduce BUILD_SET)
    __build_magic(62211): '2.7', # 2.7a0 (introduce MAP_ADD and SET_ADD)
    __build_magic(3000): '3.0',  # 3.000
    __build_magic(3010): '3.0',  # 3.000 (removed UNARY_CONVERT)
    __build_magic(3020): '3.0',  # 3.000 (added BUILD_SET)
    __build_magic(3030): '3.0',  # 3.000 (added keyword-only parameters)
    __build_magic(3040): '3.0',  # 3.000 (added signature annotations)
    __build_magic(3050): '3.0',  # 3.000 (print becomes a function)
    __build_magic(3060): '3.0',  # 3.000 (PEP 3115 metaclass syntax)
    __build_magic(3061): '3.0',  # 3.000 (string literals become unicode)
    __build_magic(3071): '3.0',  # 3.000 (PEP 3109 raise changes)
    __build_magic(3081): '3.0',  # 3.000 (PEP 3137 make __file__ and __name__ unicode)
    __build_magic(3091): '3.0',  # 3.000 (kill str8 interning)
    __build_magic(3101): '3.0',  # 3.000 (merge from 2.6a0, see 62151)
    __build_magic(3103): '3.0',  # 3.000 (__file__ points to source file)
    __build_magic(3111): '3.0',  # 3.0a4 (WITH_CLEANUP optimization).
    __build_magic(3131): '3.0',  # 3.0a5 (lexical exception stacking, including POP_EXCEPT)
    __build_magic(3141): '3.1',  # 3.1a0 (optimize list, set and dict comprehensions)
    __build_magic(3151): '3.1',  # 3.1a0 (optimize conditional branches)
    __build_magic(3160): '3.2',  # 3.2a0 (add SETUP_WITH)
    __build_magic(3170): '3.2',  # 3.2a1 (add DUP_TOP_TWO, remove DUP_TOPX and ROT_FOUR)
    __build_magic(3180): '3.2',  # 3.2a2 (add DELETE_DEREF)
    __build_magic(3190): '3.3',  # 3.3a0  3190 __class__ super closure changed
    __build_magic(3100): '3.3',  # 3.3a0  3200 (__qualname__ added)
    __build_magic(3210): '3.3',  # 3210 (added size modulo 2**32 to the pyc header)
    __build_magic(3220): '3.3',  # 3.3a1  3220 (changed PEP 380 implementation)
    __build_magic(3230): '3.3',  # 3.3a4  3230 (revert changes to implicit __class__ closure)
    __build_magic(3250): '3.4',  # 3.4a1  3250 (evaluate positional default arg
                                 # keyword-only defaults)
    __build_magic(3260): '3.4',  # 3.4a1  3260 (add LOAD_CLASSDEREF;
                                 # allow locals of class to override free vars)
    __build_magic(3270): '3.4',  # 3.4a1  3270 (various tweaks to the __class__ closure)
    __build_magic(3280): '3.4',  # 3.4a1  3280 (remove implicit class argument)
    __build_magic(3290): '3.4',  # 3.4a4  3290 (changes to __qualname__ computation)
    __build_magic(3300): '3.4',  # 3.4a4  3300 (more changes to __qualname__ computation)
    __build_magic(3310): '3.4',  # 3.4rc2 3310 (alter __qualname__ computation)
    __build_magic(3350): '3.5',  # 3.5.0
}

magics = __by_version(versions)

def __show(text, magic):
    print(text, struct.unpack('BBBB', magic), struct.unpack('HBB', magic))

def test():
    magic_20 = magics['2.0']
    current = imp.get_magic()
    magic_current = by_magic[ current ]
    print(type(magic_20), len(magic_20), repr(magic_20))
    print()
    print('This Python interpreter has version', magic_current)
    print('Magic code: ', PYTHON_MAGIC_INT)
    print(type(magic_20), len(magic_20), repr(magic_20))

if __name__ == '__main__':
    test()
