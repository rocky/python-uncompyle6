# Test semantic handling of
# [x for x in names if not y]
import os

def bug(dirname, pattern):
    if not dirname:
        if isinstance(pattern, bytes):
            dirname = bytes(os.curdir, 'ASCII')
        else:
            dirname = os.curdir
    try:
        names = os.listdir(dirname)
    except os.error:
        return []
    if not _ishidden(pattern):
        names = [x for x in names if not _ishidden(x)]
    return fnmatch.filter(names, pattern)
