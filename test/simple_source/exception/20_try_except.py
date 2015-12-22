# Tests:
#   forstmt ::= SETUP_LOOP expr _for designator for_block POP_BLOCK COME_FROM
#   for_block ::= l_stmts_opt JUMP_BACK
#   trystmt ::= SETUP_EXCEPT suite_stmts_opt POP_BLOCK try_middle COME_FROM
#   try_middle ::= jmp_abs COME_FROM except_stmts END_FINALLY

# Had a bug with the end of the except matching the end of the
# for loop.
for i in (1,2):
    try:
        x = 1
    except ValueError:
        y = 2
