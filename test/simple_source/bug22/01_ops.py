# Statements to beef up grammar coverage rules
# Force "inplace" ops
y = +10  # UNARY_POSITIVE
y /= 1   # INPLACE_DIVIDE
y %= 4   # INPLACE_MODULO
y **= 1  # INPLACE POWER
y >>= 2  # INPLACE_RSHIFT
y <<= 2  # INPLACE_LSHIFT
y //= 1  # INPLACE_TRUE_DIVIDE
`y`      # UNARY_CONVERT  - No in Python 3.x
