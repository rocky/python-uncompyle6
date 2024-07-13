# See https://github.com/rocky/python-uncompyle6/issues/498
# Bug was in not allowing _stmts in whilestmt38
import time

r = 0
while r == 1:
    print(time.time())
    if r == 1:
        r = 0
