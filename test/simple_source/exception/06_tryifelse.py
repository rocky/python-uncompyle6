# Bug from 3.4 in asyncore.py
def accept():
    try:
        conn = 5
    except TypeError:
        return None
    except OSError as why:
        if why == 6:
            raise
    else:
        return conn
