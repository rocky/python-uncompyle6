# From Python 3.6 getopt.py
# Bug showing that "while" can have several "COME_FROMS" before loop end
# NOTE: uncompyle6 still gets the "if"s wrong.
def getopt(args):
    while args and args[0] and args[0] != '-':
        if args[0] == '--':
            break
        if args[0]:
            opts = 5
        else:
            opts = 6

    return opts
