# Tests:

# return_expr_or_cond ::= return_expr
# if_exp_ret ::= expr POP_JUMP_IF_FALSE expr RETURN_END_IF return_expr_or_cond
# return_expr_or_cond ::= if_exp_ret
# ret_or ::= expr JUMP_IF_TRUE_OR_POP return_expr_or_cond COME_FROM

# See https://github.com/rocky/python-uncompyle6/issues/5

def minimize(x, y):
    return x or (x if x < y else y)
