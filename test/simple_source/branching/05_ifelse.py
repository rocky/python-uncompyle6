# Tests:

#   ifelsestmt ::= testexpr c_stmts_opt JUMP_FORWARD else_suite COME_FROM
#   else_suite ::= suite_stmts

if True:
    b = 1
else:
    d = 2
