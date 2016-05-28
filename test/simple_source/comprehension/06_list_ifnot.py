# Test semantic handling of
# [x for x in names2 if not y]
# Bug seen in Python 3
names2 = []
names = [x for x in names2 if not len(x)]
