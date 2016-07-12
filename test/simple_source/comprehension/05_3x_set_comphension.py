# Bug from Python 3.4 asyncio/tasks.py
def as_completed(fs, *, loop=None):
    todo = {async(f, loop=loop) for f in set(fs)}
