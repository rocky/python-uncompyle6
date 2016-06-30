# 2.6.9 cgi.py
# Bug in 2.6.9 was not detecting jump out of except from ValueError
def __getitem__(v):
    if v:
        try: return v
        except ValueError:
            try: return v
            except ValueError: pass
    return v
