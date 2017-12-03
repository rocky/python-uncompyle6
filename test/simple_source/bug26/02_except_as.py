# From 2.6.9 ConfigParser.py
# Note: this can only be compiled in Python 2.x
# Note also name "except_as" is a little bit of
# a misnomer since this is 2.7+ lingo for
# 2.6- syntax which we use here.

# Bug was being able to handle:
#   except KeyError, e
# vs 2.6+.
#   except KeyError as e
#
# In terms of table syntax:
# 2.7+:
# 'except_cond2':	( '%|except %c as %c:\n', 1, 5 )
# vs 2.6 and before
# 'except_cond3':	( '%|except %c, %c:\n', 1, 6 )
#
# Python 2.6 allows both, but we use the older form since
# that matches the grammar for how this gets parsed

try:
    value = "foo"

# Test ensuring parens around (a, b, c) in
# except_cond2 or except_cond3
except RuntimeError, (a, b, c):
    # Test:
    #  raise_stmt3 ::= expr expr expr RAISE_VARARGS_3
    raise a, b, c
except KeyError, e:
    raise RuntimeError('foo')
