# Bug found in 2.4 test_math.py
# Bug was turning last try/except/else into try/else
import math
def test_exceptions():
    try:
        x = math.exp(-1000000000)
    except:
        raise RuntimeError

    x = 1
    try:
        x = math.sqrt(-1.0)
    except ValueError:
        return x
    else:
        raise RuntimeError

test_exceptions()
