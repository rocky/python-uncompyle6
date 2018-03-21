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

def readline2(self):
    while True:
        line = 5
        if self[0]:
            if self:
                self[0] = 1
                continue

        return line + self[0]

# From 3.4.4 connection.py
def PipeClient(address):
    while 1:
        try:
            address += 1
        except OSError as e:
            raise e
    else:
        raise
