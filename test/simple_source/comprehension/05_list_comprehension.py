# Tests:

# Python2:
#   assert_expr_and ::= assert_expr jmp_false expr
#   and ::= expr jmp_false expr \e__come_from
#   expr ::= list_compr
#   list_iter ::= list_for
#   list_for ::= expr _for designator list_iter JUMP_BACK
#   list_iter ::= lc_body
#   lc_body ::= expr LIST_APPEND

# Use line breaks so we can see what's going on in assembly
[b
 for b in
 (0,1,2,3)
] if (__name__ == '__main__'
      ) else 5

# Python2:
#   list_compr ::= BUILD_LIST_0 list_iter
#   list_iter ::= list_for
#   list_for ::= expr _for designator list_iter JUMP_BACK
#   list_iter ::= list_for
#   list_for ::= expr _for designator list_iter JUMP_BACK
#   list_iter ::= lc_body
#   lc_body ::= expr LIST_APPEND
# [ i * j for i in range(4) for j in range(7) ]
