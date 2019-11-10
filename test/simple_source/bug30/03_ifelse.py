# Adapted from 3.0 base64
# Problem was handling if/else which
# needs to be like Python 2.6 (and not like 2.7 or 3.1)
def main(args, f):
    """Small main program"""
    if args and args[0] != '-':
        func(f, sys.stdout.buffer)
    else:
        func(sys.stdin.buffer, sys.stdout.buffer)
