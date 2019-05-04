# From 3.6.8 idlelib/query.py
# Bug was handling parenthesis around subscript in an assignment.

# RUNNABLE!
a = {'text': 1}
b  = {'text': 3}
for widget, entry, expect in (
        (a, b, 1),
        (None, b, 3)
        ):
    assert (widget or entry)['text'] == expect
    (widget or entry)['text'] = 'A'

assert a['text'] == 'A', "a[text] = %s != 'A'" % a['text']
assert b['text'] == 'A', "a[text] = %s != 'A'" % b['text']
