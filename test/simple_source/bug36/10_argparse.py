# From 3.6.4 pickletools.py
# Bug in 3.6 CALL_FUNCTION_KW in an not exponentially

import argparse
parser = argparse.ArgumentParser(
    description='disassemble one or more pickle files')
parser.add_argument(
    'pickle_file', type=argparse.FileType('br'),
    nargs='*', help='the pickle file')
parser.add_argument(
    '-m', '--memo', action='store_true',
    help='preserve memo between disassemblies')
parser.add_argument(
    '-l', '--indentlevel', default=4, type=int,
    help='the number of blanks by which to indent a new MARK level')
parser.add_argument(
    '-a', '--annotate',  action='store_true',
    help='annotate each line with a short opcode description')
parser.add_argument(
    '-p', '--preamble', default="==> {name} <==",
    help='if more than one pickle file is specified, print this before'
    ' each disassembly')
parser.add_argument(
    '-t', '--test', action='store_true',
    help='run self-test suite')
parser.add_argument(
    '-v', action='store_true',
    help='run verbosely; only affects self-test run')
args = parser.parse_args()

assert args.annotate == False
assert args.indentlevel == 4
assert args.memo == False
assert args.pickle_file == []
assert args.preamble == '==> {name} <=='
assert args.test == False
assert args.v == False
