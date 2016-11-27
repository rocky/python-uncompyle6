# Bug was using continue fouling up 1st elif, by confusing
# the "pass" for "continue" by not recognizing the if jump
# around it. We fixed by ignoring what's done in Python 2.7
# Better is better detection of control structures

def _compile_charset(charset, flags, code, fixup=None):
    # compile charset subprogram
    emit = code.append
    if fixup is None:
        fixup = 1
    for op, av in charset:
        if op is flags:
            pass
        elif op is code:
            emit(fixup(av))
        else:
            raise RuntimeError
    emit(5)
