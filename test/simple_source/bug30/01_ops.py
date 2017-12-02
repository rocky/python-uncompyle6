# Statements to beef up grammar coverage rules
# Force "inplace" ops
# Note this is like simple_source/bug22/01_ops.py
# But we don't ahve the UNARY_CONVERT which dropped
# out around 2.7
y = +10  # UNARY_POSITIVE
y /= 1   # INPLACE_DIVIDE
y %= 4   # INPLACE_MODULO
y **= 1  # INPLACE POWER
y >>= 2  # INPLACE_RSHIFT
y <<= 2  # INPLACE_LSHIFT
y //= 1  # INPLACE_TRUE_DIVIDE
y &= 1   # INPLACE_AND
y ^= 1   # INPLACE_XOR

# Beef up aug_assign and STORE_SLICE+3
x = [1,2,3,4,5]
x[0:1] = 1
x[0:3] += 1, 2, 3

# Is not in chained compare
x[0] is not x[1] is not x[2]
