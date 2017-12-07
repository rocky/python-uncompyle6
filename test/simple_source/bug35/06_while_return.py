# From Python 3.4 asynchat.py
# Tests presence or absense of
# SETUP_LOOP testexpr return_stmts POP_BLOCK COME_FROM_LOOP

def initiate_send(self, num_sent, first):
    while self.producer_fifo and self.connected:
        try:
            5
        except OSError:
            return

        if num_sent:
            if first:
                self.producer_fifo = '6'
            else:
                del self.producer_fifo[0]
        return


# FIXME: this causes a parse error:
# def initiate_send(self):
#     while self.producer_fifo and self.connected:
#         try:
#             6
#         except OSError:
#             return

#         return
