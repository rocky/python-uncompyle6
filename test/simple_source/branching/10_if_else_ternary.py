# Tests:

# ret_expr_or_cond ::= ret_expr
# if_exp_ret ::= expr POP_JUMP_IF_FALSE expr RETURN_END_IF ret_expr_or_cond
# ret_expr_or_cond ::= if_exp_ret
# ret_or ::= expr JUMP_IF_TRUE_OR_POP ret_expr_or_cond COME_FROM

# See https://github.com/rocky/python-uncompyle6/issues/5

def minimize(x, y):
    return x or (x if x < y else y)
