# From 3.0.1/lib/python3.0/_dummy_thread.py

def start_new_thread(function, args, kwargs={}):
    try:
        function()
    except SystemExit:
        pass
    except:
        args()

# Adapted from 3.0.1 code.py
# Bug is again JUMP_FORWARD elimination compared
# to earlier and later Pythons.
def interact():
    while 1:
        try:
            more = 1
        except KeyboardInterrupt:
            more = 0
