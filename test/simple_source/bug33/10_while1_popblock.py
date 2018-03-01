# From 3.4.4 mailcap.py
# Bug was needing a grammar rule to add POP_BLOCK before the end of the while1.
# 3.3 apparently doesn't add this.
def readmailcapfile(line):
    while 1:
        if not line: break
        if line[0] == '#' or line.strip() == '':
            continue
        if not line:
            continue
        for j in range(3):
            line[j] = line[j].strip()
        if '/' in line:
            line['/'].append('a')
        else:
            line['/'] = 'a'
    return
