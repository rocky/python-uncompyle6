# Python 2.5 bug
# Was turning into tryelse when there in fact is no else.
def options(self, section):
    """Return a list of option names for the given section name."""
    try:
        opts = self._sections[section].copy()
    except KeyError:
        raise NoSectionError(section)
    opts.update(self._defaults)
    if '__name__' in opts:
        del opts['__name__']
    return opts.keys()
