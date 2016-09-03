# From python 2.6 StringIO.py
# Bug was turning emitting code like:
#     if spos == slen:
#          self.len = self.pos = spos + len(s)
#         return None
#         # wrong indent below
#         if spos > slen:
#            ...
#         if self.buflist:
#            # Invalid "and" below
#            self.buflist and self.buf += ''.join(self.buflist)
#
# This was caused by POP_TOP in RETURN_VALUE, POP_TOP getting treated
# as the beginning of a statement
def write(self, s, spos):
    if not s: return
    # Force s to be a string or unicode
    if not isinstance(s, basestring):
        s = str(s)
    slen = self.len
    if spos == slen:
        self.len = self.pos = spos + len(s)
        return
    if spos > slen:
        slen = spos
    newpos = spos + len(s)
    if spos < slen:
        if self.buflist:
            self.buf += ''.join(self.buflist)
        self.buflist = [self.buf[:spos], s, self.buf[newpos:]]
        if newpos > slen:
            slen = newpos
    else:
        self.buflist.append(s)
