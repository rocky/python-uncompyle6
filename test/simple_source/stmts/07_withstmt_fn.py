# Python 2.6 has a truly weird way of handling "with" here.
# added rule for 2.6
#   setupwith ::= DUP_TOP LOAD_ATTR ROT_TWO LOAD_ATTR CALL_FUNCTION_0 POP_TOP

import sys
from warnings import catch_warnings
with catch_warnings():
    if sys.py3kwarning:
        sys.filterwarnings("ignore", ".*mimetools has been removed",
                           DeprecationWarning)
    import mimetools
