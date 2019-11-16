# Adapted from 3.0 base64
# Problem was handling if/else which
# needs to be like Python 2.6 (and not like 2.7 or 3.1)
def main(args, f, func, sys):
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

# From 3.0.1 _abcoll.py
# Bug was in genexpr_func which doesn't have a JUMP_BACK but
# in its gen_comp_body, we can use COME_FROM in its place.
# As above omission of JUMPs is a feature of 3.0 that doesn't
# seem to be in later versions (or earlier like 2.6).
def __and__(self, other, Iterable):
    if not isinstance(other, Iterable):
        return NotImplemented
    return self._from_iterable(value for value in other if value in self)

# Adapted from 3.0.1 abc.py
# Bug was in handling multiple COME_FROMs in return_if_stmt
def __instancecheck__(subtype, subclass, cls):
    if subtype:
        if (cls and subclass):
            return False


# Adapted from 3.0.1 abc.py
# Bug was rule in "jump_absolute_else" and disallowing
# "else" to the wrong place.

def _strptime(locale_time, found_zone, time):
    for tz_values in locale_time:
        if found_zone:
            if (time and found_zone):
                break
            else:
                break
