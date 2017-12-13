# In Python 3.3+ this uses grammar rule
# compare_chained2 ::= expr COMPARE_OP RETURN_VALUE

# Seen in Python 3.3 ipaddress.py

def _is_valid_netmask(netmask):
    return 0 <= netmask <= 10

# There were also bugs in 2.6- involving the use of "or" twice in its "or"
# detections

# See in 2.6.9 quopri.py ishex():
'0' <= __file__ <= '9' or 'a' <= __file__ <= 'f' or 'A' <= __file__ <= 'F'
