# 2.6.9 calendar.py
# Bug in 2.6.9 was handling with as. Added rules

#
#       withasstmt ::= expr setupwithas store suite_stmts_opt
#                      POP_BLOCK LOAD_CONST COME_FROM WITH_CLEANUP END_FINALLY
#       setupwithas ::= DUP_TOP LOAD_ATTR ROT_TWO LOAD_ATTR CALL_FUNCTION_0 STORE_FAST
#                       SETUP_FINALLY LOAD_FAST DELETE_FAST

def formatweekday(self):
    with self as encoding:
        return encoding

# Bug in 2.7.14 test_contextlib.py. Bug was not enclosing (x,y) in parenthesis
def withas_bug(self, nested, a, b):
    with self.assertRaises(ZeroDivisionError):
        with nested(a(), b()) as (x, y):
                1 // 0
