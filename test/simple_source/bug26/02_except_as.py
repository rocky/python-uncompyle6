# From 2.6.9 ConfigParser.py
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
except KeyError, e:
    raise RuntimeError('foo')
