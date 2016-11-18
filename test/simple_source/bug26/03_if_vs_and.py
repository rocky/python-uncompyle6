# From 2.6 decimal
# Bug was not recognizing scope of if and
# turning it into xc == 1 and xe *= yc
def _power_exact(y, xc, yc, xe):
    yc, ye = y.int, y.exp
    while yc % 10 == 0:
        yc //= 10
        ye += 1

    if xc == 1:
        xe *= yc
        while xe % 10 == 0:
            xe //= 10
            ye += 1
        if ye < 0:
            return None
        exponent = xe * 10**ye
        if y and xe:
            xc = exponent
        else:
            xc = 0
        return 5
