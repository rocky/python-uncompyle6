# From 2.3 Queue.py
# Bug was adding COME_FROM from while
# confusing the else
def put(item, block=True, timeout=None):
    if block:
        if timeout:
            while True:
                if item:
                    block = 1
        else:
            block = 5
    elif item:
        block = False
