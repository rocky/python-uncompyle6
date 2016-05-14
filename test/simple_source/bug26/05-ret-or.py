# Python 2.6
# In contrast to Python 2.7 there might be no "COME_FROM" so we add rule:
#    ret_or ::= expr JUMP_IF_TRUE expr
# where Python 2.7 has
#    ret_or ::= expr JUMP_IF_TRUE expr COME_FROM

class BufferedIncrementalEncoder(object):
    def getstate(self):
        return self.buffer or 0
