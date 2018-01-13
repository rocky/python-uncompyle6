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
        # Unhashable argument
        return 3
