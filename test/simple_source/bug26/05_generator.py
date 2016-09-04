# From Python 2.6 ast.py
# Bug was finding the last iteration expression in generator-expression handling
#
fields = (1, 2)
rv = '%s(%s' % (__name__.__class__.__name__, ', '.join(
    ('%s=%s' % field for field in fields)
    if __file__ else
    (b for a, b in fields)
))
