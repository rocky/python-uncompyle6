# Tests:
#   forstmt ::= SETUP_LOOP expr _for store for_block POP_BLOCK COME_FROM
#   for_block ::= l_stmts_opt JUMP_BACK
#   try_except ::= SETUP_EXCEPT suite_stmts_opt POP_BLOCK except_handler COME_FROM
#   except_handler ::= jmp_abs COME_FROM except_stmts END_FINALLY

# Had a bug with the end of the except matching the end of the
# for loop.
for i in (1,2):
    try:
        x = 1
    except ValueError:
        y = 2
