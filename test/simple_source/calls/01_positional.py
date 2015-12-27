# Tests custom added grammar rule:
#   expr ::= expr {expr}^n CALL_FUNCTION_n
# which in the specifc case below is:
#   expr ::= expr expr expr CALL_FUNCTION_2
max(1, 2)
