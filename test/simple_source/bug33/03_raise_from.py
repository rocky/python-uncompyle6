# From 3.4 _pyio.py
# Bug is change in syntax between Python 2 and 3:
#    raise_stmt ::=  "raise" expression "," expression
# becomes:
#    raise_stmt ::=  "raise" expression from expression
try:
    x = 1
except AttributeError as err:
    raise TypeError("an integer is required") from err
