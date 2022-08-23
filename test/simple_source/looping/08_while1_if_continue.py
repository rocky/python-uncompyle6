# 2.6.9 text_file.py
# Bugs in 2.6 and 2.7 detecting structure
def readline (self):
    while 1:
        if self:
            if __file__:
                continue

        return

# From 2.4.6 sre.py
# Bug has to do with "break" not being recognized
# and is a JUMP_FORWARD.
def _parse(a, b, source, state):
    while 1:
        if b:
            while 1:
                break
        else:
            raise

def _parse2(source, state, a, b, this):
    while 1:
        if a:
            if b:
                while 1:
                    this = 1
                    break
                continue

        while 1:
            if b:
                break

        x = this

# Bug was in 2.3 decompilation
def _parse3(source, state, a, b):
    while 1:
        if a:
            if b:
                x = 1
                while 1:
                    if a:
                        break
                    raise
