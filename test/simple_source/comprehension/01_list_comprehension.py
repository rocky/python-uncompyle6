# Simple list commprehensions
#
# Python2 grammar includes:
#  list_compr ::= BUILD_LIST_0 list_iter
#  list_iter ::= list_for
#  list_for ::= expr _for store list_iter JUMP_BACK
#  list_iter ::= lc_body
#  lc_body ::= expr LIST_APPEND
#
# Python 3 grammar includes:
#  listcomp ::= LOAD_LISTCOMP LOAD_CONST MAKE_FUNCTION_0 expr GET_ITER CALL_FUNCTION_1

# Add line spacing to assist in seeing which parts go where
# in assembly and code

[ i
  for
  i in
  (1, 2, 3, 4)
]

[ i+1
  for
  i in
  (1, 2, 3, 4)
]

[ i * i
  for
  i in
  range(4) ]
