# Tests and empty finally section
# tryfinallystmt ::= SETUP_FINALLY e_suite_stmts_opt
#                    POP_BLOCK LOAD_CONST COME_FROM e_suite_stmts_opt END_FINALLY
#

try:
    pass
finally:
    pass
pass
