# From 3.6.8 idlelib/query.py
# Bug was handling parens around subscript

# RUNNABLE!
a = {'text': 1}
b  = {'text': 3}
for widget, entry, expect in (
        (a, b, 1),
        (None, b, 3)
        ):
    assert (widget or entry)['text'] == expect
