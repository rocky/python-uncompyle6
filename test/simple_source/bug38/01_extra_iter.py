# Adapted from From 3.3 urllib/parse.py
qs = "https://travis-ci.org/rocky/python-uncompyle6/builds/605260823?utm_medium=notification&utm_source=email"
expect = ['https://travis-ci.org/rocky/python-uncompyle6/builds/605260823?utm_medium=notification', 'utm_source=email']

# Should visually see that we don't add an extra iter() which is not technically wrong, just
# unnecessary.
assert expect == [s2 for s1 in qs.split('&') for s2 in s1.split(';')]
