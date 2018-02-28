# From 3.6 _sitebuiltins.py
# Bug was in handling double nested kinds of things like:
#     for a in b for c in d

# This required grammar modification and
# and semantic action changes. LOAD_CLOSUREs are stored
# inside a MAKE_TUPLE.

# FIXME: test and try additional "if" clauses.
def __init__(self, path, name, files=(), dirs=(), volumes=()):
    f = [path.join(dir, filename)
        for dir in dirs
        for filename in files]
    f2 = [path.join(drive, dir, filename)
         for dir in dirs
         for filename in files
         for drive in volumes]
    return f, f2

# From 3.6 codeop. The below listcomp is generated still
# like it was in 3.5
import __future__
_features = [getattr(__future__, fname)
             for fname in __future__.all_feature_names]
