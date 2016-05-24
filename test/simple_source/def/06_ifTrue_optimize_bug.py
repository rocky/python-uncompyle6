# Bug in uncompyle6 and pycdc for (some) Python 3 bytecodes.
# Problem is JUMP_IF_FALSE is optimized away leaving
# the unreachible LOAD_CONST below

# Disassembly of lambda is:
#  0       LOAD_CONST              2: 2
#  3       RETURN_VALUE
#  4       LOAD_CONST              3: 3
#  7       RETURN_VALUE

lambda: 2 if True else 3
