# Tests
# while1stmt ::= SETUP_LOOP l_stmts JUMP_BACK POP_BLOCK COME_FROM
# tryfinallystmt ::= SETUP_FINALLY suite_stmts_opt POP_BLOCK

try:
    while 1:
        if __file__:
            break
finally:
    pass
