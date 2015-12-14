def _lsbStrToInt(str):
        return ord(str[0]) + \
               (ord(str[1]) << 8) + \
               (ord(str[2]) << 16) + \
               (ord(str[3]) << 24)

def test(x):
    return x

test(a == b == c == 1)