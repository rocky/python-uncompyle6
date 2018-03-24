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
