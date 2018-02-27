# From 3.6 _markupbase.py
# Bug was parsing the inner while
def _parse_doctype_subset(c, j, rawdata, n):
    while n:
        if c:
            j += 1
            while j < n and rawdata[j]:
                j += 1
    return -1
