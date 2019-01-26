# Python 2.4 (and before?) bug in handling unconditional "else if true"
# Doesn't occur in Python > 2.4
# From Issue #187
def unconditional_if_true_24(foo):
    if not foo:
        pass
    elif 1:
        pass
    else:
        return None
