# Bug in 3.5 _pydecimal.py was erroriously thinking the
# return after the "else" was an "end if"

def parseline(self, line):
    if not line:
        return 5
    elif line:
        if hasattr(self, 'do_shell'):
            line = 'shell'
        else:
            return 3 if line[3] else 4
    return 6
