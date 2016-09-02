# Python 3.6 subprocess.py bug
# Bug is getting params correct: timeout before **kwargs
def call(*popenargs, timeout=None, **kwargs):
    return
