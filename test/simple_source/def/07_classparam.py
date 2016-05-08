# Tests Python 3:
# build_class ::= LOAD_BUILD_CLASS mkfunc expr call_function CALL_FUNCTION_3

from collections import namedtuple
class Event(namedtuple('Event', 'time, priority, action, argument')):
    pass
