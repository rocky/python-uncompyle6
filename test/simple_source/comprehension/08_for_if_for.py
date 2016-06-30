# from 2.6.9 ast
# Should see genexpr
rv = '%s(%s' % (node.__class__.__name__, ', '.join(
    ('%s=%s' % field for field in fields)
    if annotate_fields else
    (b for a, b in fields)
))
