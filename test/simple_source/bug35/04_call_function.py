# From sql/schema.py and 3.5 _strptime.py
# Bug was code not knowing which Python versions
# have kwargs coming before positional args in code.

# RUNNABLE!

def tometadata(self, metadata, schema, Table, args, name=None):
    table = Table(
        name, metadata, schema=schema,
        *args, **self.kwargs
    )
    return table

def _strptime_datetime(cls, args):
    return cls(*args)


# From 3.5.5 imaplib
# Bug is in parsing *date_time[:6] parameter
from datetime import datetime, timezone, timedelta
import time
def Time2Internaldate(date_time):
    delta = timedelta(seconds=0)
    return datetime(*date_time[:6], tzinfo=timezone(delta))

assert Time2Internaldate(time.localtime())

# From 3.5.5 tkinter/dialog.py
def test_varargs0_ext():
    try:
        {}.__contains__(*())
    except TypeError:
        pass

test_varargs0_ext()

# From 3.4.6 tkinter/dialog.py
# Bug is in position of *cnf.

def __init__(self, cnf={}):
    self.num = self.tk.call(
        'tk_dialog', self._w,
        cnf['title'], cnf['text'],
        cnf['bitmap'], cnf['default'],
        *cnf['strings'])

# From python 3.4.8 multiprocessing/context.py
def Value(self, fn, typecode_or_type, *args, lock=True):
    return fn(typecode_or_type, *args, lock=lock,
              ctx=self.get_context())

# From 3.6.4 heapq.py
def merge(*iterables, key=None, reverse=False):
    return

def __call__(self, *args, **kwds):
    pass

# From 3.6.4 shutil
def unpack_archive(func, filename, dict, format_info, extract_dir=None):
    func(filename, extract_dir, **dict(format_info[2]))

# From 3.5.5 test_xrdrlib.py
import xdrlib
def assertRaisesConversion(self, *args):
   self.assertRaises(xdrlib.ConversionError, *args)

# From 3.2.6 _pyio.py
class BlockingIOError(IOError):
    def __init__(self, errno, strerror, characters_written=5):
        super().__init__(errno, strerror)

# From urllib/parse.py
# Bug was using a subclass made from a call (to namedtuple)
from collections import namedtuple

class ResultMixin(object):
    pass

class SplitResult(namedtuple('SplitResult', 'scheme netloc path query fragment'), ResultMixin):
    pass
