# 2.6.9 asynchat.py
# 2.6 added:
# return_stmt ::= return_expr RETURN_END_IF come_from_pop
def initiate_send(self, x):
    while self:
        if self:
            x = 'a'
        else:
            del self.producer_fifo[0]
        return x

# 2.6.9 contextlib.py
# Bug was in return exc, so added:
# return_stmt ::= return_expr RETURN_VALUE_IF come_from_pop

def __exit__(self, type, value, traceback):
    try:
        raise RuntimeError
    except StopIteration:
        return value
    except:
        raise
