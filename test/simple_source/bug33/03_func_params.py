# Bug from Python 3.3 codecs.py
# Bug is in 3.3 handling of this complicated parameter list
def __new__(cls, encode, decode, streamreader=None, streamwriter=None,
    incrementalencoder=None, incrementaldecoder=None, name=None,
    *, _is_text_encoding=None):
    return

# From 3.3 _pyio.py. A closure is created here.
# This changes how the default params are found
class StringIO(object):
    def __init__(self, initial_value="", newline="\n"):
        super(StringIO, self).__init__()

# No closure created here
class StringIO2(object):
    def __init__(self, initial_value="", newline="\n"):
        return 5
