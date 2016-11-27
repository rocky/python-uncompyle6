# Bug from 3.4 threading. Bug is handling while/else
def acquire(self):
    with self._cond:
        while self:
            rc = False
        else:
            rc = True
    return rc
