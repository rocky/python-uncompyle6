# Tests:

#   ifelsestmt ::= testexpr c_stmts_opt JUMP_FORWARD else_suite COME_FROM
#   else_suite ::= suite_stmts

if True:
    b = 1
else:
    d = 2


a = 1

if a == 1:
    a = 3
elif a == 2:
    a = 4

if a == 1:
    a = 5
elif a == 2:
    a = 6
else:
    a = 7

if a == 1:
    a = 8
elif a == 7:
    a = 9
elif a == 3:
    a = 10
else:
    a = 11

if a == 11:
    a = 12
elif a == 12:
    a = 13
elif a == 13:
    a = 14

if a == 1:
    b  = 1
else:
    if a == 2:
       b = 2
    else:
        if a == 3:
            b = 3
        else:
            b = 4

if a == 1:
    a = 1
else:
    if a == 2:
        a = 2
    else:
        b = 3
        if a == 3:
            b = 4
        else:
            b = 5

if a == 1:
    b = 1
else:
    b = 2
    if a == 2:
        b = 3
    else:
        if a == 3:
            b = 4
        else:
            b = 5

if a == 1:
    b = 2
else:
    b = 3
    if a == 2:
        b = 4
    else:
        b = 5
        if a == 3:
            b = 6
        elif a == 4:
            b = 7
        elif a == 4:
            b = 8
        else:
            b = 9
