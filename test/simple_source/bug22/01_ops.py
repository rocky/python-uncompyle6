# Statements to beef up grammar coverage rules
# Force "inplace" ops
y = +10  # UNARY_POSITIVE
y /= 1   # INPLACE_DIVIDE
y %= 4   # INPLACE_MODULO
y **= 1  # INPLACE POWER
y >>= 2  # INPLACE_RSHIFT
y <<= 2  # INPLACE_LSHIFT
y //= 1  # INPLACE_TRUE_DIVIDE
y &= 1   # INPLACE_AND
y ^= 1   # INPLACE_XOR

`y`      # UNARY_CONVERT  - No in Python 3.x

# Beef up aug_assign and STORE_SLICE+3
x = [1,2,3,4,5]
x[0:1] = 1
x[0:3] += 1, 2, 3

# Is not in chained compare
x[0] is not x[1] is not x[2]

# Method name is a constant, so we need parenthesis around it
(1).__nonzero__() ==  1
