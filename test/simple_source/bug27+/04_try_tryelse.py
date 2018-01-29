# From 2.7 test_normalize.py
# Bug has to to with finding the end of the tryelse block. I think thrown
# off by the "continue". In instructions the COME_FROM for END_FINALLY
# was at the wrong offset because some sort of "rtarget" was adjust.

# When control flow is in place this logic in the code will be simplified
def test_main(self, c1):
    for line in self:
        try:
            c1 = 6
        except:
            if c1:
                try:
                    c1 = 5
                except:
                    pass
                else:
                    c1 = 1
            continue

        pass
