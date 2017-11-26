# From 3.4 mailbox.py
# Bug is not not getting control structure right
# specifically the 2nd elif not line
def _generate_toc(line):
    while 1:
        if line.startswith('2'):
            line = 5
            while 1:
                if line:
                    line = 6
                    break
                elif not line:
                    line = 7
                    break
        elif not line:
            break

    return 1
