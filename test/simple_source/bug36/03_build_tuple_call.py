# From Python 3.6.5 email/message.py
# Bug is in handling 'related' parameter
def add_related(self, *args, **kw):
    self._add_multipart('related', *args, _disp='inline', **kw)
