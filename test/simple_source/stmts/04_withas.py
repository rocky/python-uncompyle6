# 2.6.9 calendar.py
# Bug in 2.6.9 was handling with as. Added rules

#
#       withasstmt ::= expr setupwithas designator suite_stmts_opt
#                      POP_BLOCK LOAD_CONST COME_FROM WITH_CLEANUP END_FINALLY
#       setupwithas ::= DUP_TOP LOAD_ATTR ROT_TWO LOAD_ATTR CALL_FUNCTION_0 STORE_FAST
#                       SETUP_FINALLY LOAD_FAST DELETE_FAST

def formatweekday(self):
    with self as encoding:
        return encoding
