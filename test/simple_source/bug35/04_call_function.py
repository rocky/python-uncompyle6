# From sql/schema.py and 3.5 _strptime.py
# Note that kwargs comes before "positional" args

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
def test_varargs0_ext(self):
    try:
        {}.__contains__(*())
    except TypeError:
        pass

# From 3.4.6 tkinter/dialog.py
# Bug is in position of *cnf.

def __init__(self, master=None, cnf={}):
    self.num = self.tk.call(
        'tk_dialog', self._w,
        cnf['title'], cnf['text'],
        cnf['bitmap'], cnf['default'],
        *cnf['strings'])
