# In Python 3.3+ this uses grammar rule
# compare_chained2 ::= expr COMPARE_OP RETURN_VALUE

def _is_valid_netmask(self, netmask):
    return 0 <= netmask <= self._max_prefixlen
