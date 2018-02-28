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
