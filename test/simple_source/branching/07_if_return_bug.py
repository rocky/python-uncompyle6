# From 3.5.1 bdb
#
# RETURN_VALUES can get turned in RETURN_END_IF
# scanner3's detect_structure sometimes can't
# fully handle Python 3.5's jump optimization
# So in 3.5, for now, we allow:
#
#    return_stmt ::= return_expr RETURN_END_IF
# and you see that in the grammar rules for below.

# For other pythons the RETURN_END_IF may be a
# RETURN_VALUE.
# Or it may be that we may want to add that
# additional return_stmt grammar rule for Pythons
# before 3.5 which currently isn't needed.

def effective(line):
    for b in line:
        if not b.cond:
            return
        else:
            try:
                val = 5
                if val:
                    if b.ignore:
                        b.ignore -= 1
                    else:
                        return (b, True)
            except:
                return (b, False)
    return
