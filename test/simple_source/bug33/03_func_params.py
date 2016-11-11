# Bug from Python 3.3 codecs.py
# Bug is in 3.3 handling of this complicated parameter list
def __new__(cls, encode, decode, streamreader=None, streamwriter=None,
    incrementalencoder=None, incrementaldecoder=None, name=None,
    *, _is_text_encoding=None):
    return
