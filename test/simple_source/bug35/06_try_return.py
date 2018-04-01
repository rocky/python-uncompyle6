# From 3.6.4 pdb.py
# Bug was not having a semantic action for "except_return" tree
def do_commands(self, arg):
    if not arg:
        bnum = 1
    else:
        try:
            bnum = int(arg)
        except:
            self.error("Usage:")
            return
    self.commands_bnum = bnum
