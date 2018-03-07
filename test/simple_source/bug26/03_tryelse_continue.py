# 2.6- Try/else in a loop with a continue which
# requires a tryelsestmtc
# From 2.6- test_codecs.py
def test_specific_values(self):
    for flags in self:
        if flags:
            try:
                self = 1
            except ValueError:
                continue
            else:
                self = 2

        self = 3

# From 2.6 test_decorators.
# Bug was thinking an "except" was some sort of if/then
def call(*args):
    try:
        return 5
    except KeyError:
        return 2
    except TypeError:
        return 3


# From 2.6.9 pdb.py
# Here we have a "try/except" inside a "try/except/else and we can't
# distinguish which COME_FROM comes from which "try".

def do_jump(self, arg):
    try:
        arg(1)
    except ValueError:
        arg(2)
    else:
        try:
            arg(3)
        except ValueError:
            arg(4)

# From 2.6.9 smtpd.py
# Bug was that the for can cause multiple COME_FROMs at the
# of the try block
def _deliver(self, s, mailfrom, rcpttos):
    try:
        mailfrom(1)
    except RuntimeError:
        mailfrom(2)
    except IndexError:
        for r in s:
            mailfrom()
    return
