# From python 3.4 sre.pyc
while 1:
    if __file__:
        while 1:
            if __file__:
                break
            raise RuntimeError
    else:
        raise RuntimeError

# Adapted from 3.0.1 cgi.py
def _parseparam(s, end):
    while end > 0 and s.count(''):
        end = s.find(';')
