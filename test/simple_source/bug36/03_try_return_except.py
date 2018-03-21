# From Python 3.6 bdb.py
# Bug was handling try's with returns
# END_FINALLY in 3.6 starts disasppearing

def effective(possibles):
    for b in possibles:
        try:
            return 1
        except:
            return 2
    return 3

assert effective([5]) == 1
assert effective([]) == 3

def effective2(possibles):
    b = 0
    for b in possibles:
        try:
            if b >= 5:
                b = 5
            else:
                return 2
        except:
            return 3
    return b

assert effective2([5]) == 5
assert effective2([]) == 0
assert effective2(['a']) == 3
