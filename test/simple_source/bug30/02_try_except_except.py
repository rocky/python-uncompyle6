# From 3.0.1/lib/python3.0/_dummy_thread.py

def start_new_thread(function, args, kwargs={}):
    try:
        function()
    except SystemExit:
        pass
    except:
        args()
