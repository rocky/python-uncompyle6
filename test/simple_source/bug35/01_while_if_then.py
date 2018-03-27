# From python 3.5.5 telnetlib
# The bug is the end of a "then" jumping
# back to the loop which could look like
# a "continue" and also not like a then/else
# break
def process_rawq(self, cmd, cmd2):
    while self.rawq:
        if self.iacseq:
            if cmd:
                pass
            elif cmd2:
                if self.option_callback:
                    self.option = 2
                else:
                    self.option = 3

# From python 3.5.5 telnetlib
def listener(data):
    while 1:
        if data:
            data = 1
        else:
            data = 2
