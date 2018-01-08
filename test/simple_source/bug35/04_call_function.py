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
