# From 2.5.6 osxemxpath.py
# Bug is in getting "and" and "del" correct

# This is RUNNABLE!
def normpath(comps):
    i = 0
    while i < len(comps):
        if comps[i] == '.':
            del comps[i]
        elif comps[i] == '..' and i > 0 and comps[i-1] not in ('', '..'):
            del comps[i-1:i+1]
            i = i - 1
        elif comps[i] == '' and i > 0 and comps[i-1] != '':
            del comps[i]
        else:
            i = i + 1
    return comps

assert normpath(['.']) == []
assert normpath(['a', 'b', '..']) == ['a']
assert normpath(['a', 'b', '', 'c']) == ['a', 'b', 'c']
assert normpath(['a', 'b', '.', '', 'c', '..']) == ['a', 'b']

# Adapted from 3.0.1 cgi.py
# Bug was in detecting "or" and "and" due to lack of PUSH/POP_IF instructions.
def handle(format, html, text):
    formatter = (format and html) or text
    return formatter

assert handle(False, False, True)
assert not handle(True, False, False)
assert handle(True, True, False)
