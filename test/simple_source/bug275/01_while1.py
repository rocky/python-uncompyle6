# Issue #173. Bug is that 2.7.5 omits POP_BLOCK in
# in later 2.7 grammar.
#  while1stmt        ::= SETUP_LOOP l_stmts_opt JUMP_BACK COME_FROM
#  while1stmt        ::= SETUP_LOOP l_stmts_opt CONTINUE COME_FROM
# which is included in later code generation
ms=0
if ms==1:
    while 1:
        pass
