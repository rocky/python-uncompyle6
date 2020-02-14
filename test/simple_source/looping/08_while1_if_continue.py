# 2.6.9 text_file.py
# Bugs in 2.6 and 2.7 detecting structure
def readline (self):
    while 1:
        if self:
            if __file__:
                continue

        return

# From 2.4.6 sre.py
# Bug in 2.4 and 2.3 was parsing the nested "while 1" with a "break" in it
def _parse(a, b, source, state):
    while 1:
        if b:
            while 1:
                break
        else:
            raise
