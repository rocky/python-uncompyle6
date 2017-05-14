# sql/schema.py
def tometadata(self, metadata, schema, Table, args, name=None):
    table = Table(
        name, metadata, schema=schema,
        *args, **self.kwargs
    )
    return table
