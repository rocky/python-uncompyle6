# From 2.6 test_datetime.py
# Bug is in parsing (x is 0 or x is 1) and (y is 5 or y is 2)
# correctly.

# This code is RUNNABLE!
result = []
for y in (1, 2, 10):
    x = cmp(1, y)
    if (x is 0 or x is 1) and (y is 5 or y is 2):
        expected = 10
    elif y is 2:
        expected = 2
    else:
        expected = 3
    result.append(expected)

assert result == [10, 2, 3]
