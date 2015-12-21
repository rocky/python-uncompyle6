# Tests:
# list_compr ::= BUILD_LIST_0 list_iter
# list_iter ::= list_for
# list_for ::= expr _for designator list_iter JUMP_BACK
[b for b in (0,1,2,3)] if True else 5
