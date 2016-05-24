# But is that we were removing the return 3 at the end of the function
# and a the end of *any* function. We do want to remove "return None"
# at the end of a main program, but that's something different.
def fn(self):
    if self.id == 'hat':
        return 4
    return 3
