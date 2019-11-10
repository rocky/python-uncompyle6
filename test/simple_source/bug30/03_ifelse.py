# Adapted from 3.0 base64
# Problem was handling if/else which
# needs to be like Python 2.6 (and not like 2.7 or 3.1)
def main(args, f):
    """Small main program"""
    if args and args[0] != '-':
        func(f, sys.stdout.buffer)
    else:
        func(sys.stdin.buffer, sys.stdout.buffer)

# From Python 3.0 _markupbase.py.
#
# The Problem was in the way "if"s are generated in 3.0 which is sort
# of like a more optimized Python 2.6, with reduced extraneous jumps,
# but still 2.6-ish and not 2.7- or 3.1-ish.
def parse_marked_section(fn, i, rawdata, report=1):
    if report:
        j = 1
        fn(rawdata[i: j])
    return 10
