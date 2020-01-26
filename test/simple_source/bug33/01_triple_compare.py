# In Python 3.3+ this uses grammar rule
# compare_chained2 ::= expr COMPARE_OP RETURN_VALUE
# In Python 3.6 uses this uses grammar rule
# compare_chained2 ::= expr COMPARE_OP come_froms JUMP_FORWARD

# Seen in Python 3.3 ipaddress.py

# RUNNABLE!
def _is_valid_netmask(netmask):
    return 0 <= netmask <= 10

# There were also bugs in 2.6- involving the use of "or" twice in its "or"
# detections

# See in 2.6.9 quopri.py ishex():
assert not '0' <= __file__ <= '9' or 'a' <= __file__ <= 'f' or 'A' <= __file__ <= 'F'

# From 3.7 bug-grammar.py

# Bug in 3.7 was handling the last line where compare_chained -> compare_chained37 and
# therefore compare_chained has one child, not two as it normally does.

def test_comparison():
    ### comparison: expr (comp_op expr)*
    ### comp_op: '<'|'>'|'=='|'>='|'<='|'!='|'in'|'not' 'in'|'is'|'is' 'not'
    if 1: pass
    x = (1 == 1)
    if 1 == 1: pass
    if 1 != 1: pass
    if 1 < 1: pass
    if 1 > 1: pass
    if 1 <= 1: pass
    if 1 >= 1: pass
    if 1 in (): pass
    if 1 not in (): pass
    if 1 < 1 > 1 == 1 >= 1 <= 1 != 1 in 1 not in 1 is 1 is not 1: pass
