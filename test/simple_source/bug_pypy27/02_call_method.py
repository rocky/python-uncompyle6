# Bug in PyPy was not handling CALL_METHOD_xxx like
# CALL_FUNCTION_XXX
def truncate(self, size=None):
    self.db.put(self.key, '', txn=self.txn, dlen=self.len - size, doff=size)
