# Python 1.4 aifc.py
# Something weird about the final "print" and PRINT_NL_CONT followed by PRINT_NL
def _readmark(self, markers):
    if self._markers: print 'marker',
    else: print 'markers',
    print 'instead of', markers
