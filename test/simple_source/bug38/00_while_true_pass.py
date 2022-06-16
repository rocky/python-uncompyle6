# The 3.8 bugs were in detecting
# 1) while True: pass
# 2) confusing the "if" ending in a loop jump with a "while"
if __name__:
    while True:
        pass
