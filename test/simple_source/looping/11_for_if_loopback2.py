# Python 3 bugs with multiple COME_FROMs
# Tests:
#         160	POP_TOP           ''
#         161	JUMP_BACK         '118' # to: for name in names
#         164	JUMP_BACK         '118' # to: for name in names after endif
#         167	POP_BLOCK         ''    # ends for loop
#       168_0	COME_FROM         '63'  # end of if os.path is...
#       168_1	COME_FROM         '108' # end of first result.append(name) in if/then
#       168_2	COME_FROM         '111' # end of "for name in names" in else

import os
import posixpath

def filter(names, pat):
    result = []
    pat = os.path.normcase(pat)
    match = _compile_pattern(pat, isinstance(pat, bytes))
    if os.path is posixpath:
        for name in names:
            if match(name):
                result.append(name)
    else:
        for name in names:
            if match(os.path.normcase(name)):
                result.append(name)  # bug here
