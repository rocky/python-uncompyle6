# Python 3.6 subprocess.py bug
# Bug is getting params correct: timeout before **kwargs
import subprocess
def call(*popenargs, timeout=None, **kwargs):
    return

# From 3.4 asyncio/base_events.py
# Bug was in pickin up name of ** (kwargs)
def subprocess_shell(self, protocol_factory, cmd, *, stdin=subprocess.PIPE,
                     stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                     universal_newlines=False, shell=True, bufsize=0,
                     **kwargs):
    return

# From 3.4 asyncio/locks.py
# Bug was handling" "value=1, *"

class Semaphore:
    pass

class BoundedSemaphore(Semaphore):
    def __init__(self, value=1, *, loop=None):
        super().__init__(value, loop=loop)
