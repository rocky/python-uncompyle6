from __future__ import with_statement
with open(__file__, 'r') as f:
    print(f)
    with f:
        pass
