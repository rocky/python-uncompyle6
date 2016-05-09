# Test Bug in handling whileTrue jumping around an else

# Python 3.2 has
#  whileTruestmt ::= SETUP_LOOP l_stmts_opt JUMP_BACK _come_from
# where Python 3.5 has
#  whileTruestmt ::= SETUP_LOOP l_stmts_opt JUMP_BACK POP_BLOCK _come_from

import sys

rv = 0
if sys.argv == ['-']:
    while True:
        filename = sys.argv[0]
        try:
            compile(filename, doraise=True)
        except IOError:
            rv = 1
else:
    rv = 1
