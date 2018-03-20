# Bug in Python 3.4 text_file.py
# Bug is handling:  while true ... if ... continue
def readline(b):
    a = 1
    while True:
        if b:
            if b[0]:
                a = 2
                b = None
                continue
        b = None
        a = 5

        return a

assert readline(None) == 1
assert readline([2]) == 2
