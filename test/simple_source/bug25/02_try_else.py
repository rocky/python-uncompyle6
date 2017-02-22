# Python 2.5 bug
# Was turning into tryelse when there in fact is no else.
def options(self, section):
    try:
        opts = self._sections[section].copy()
    except KeyError:
        raise NoSectionError(section)
    opts.update(self._defaults)
    if '__name__' in opts:
        del opts['__name__']
    return opts.keys()

# From python2.5/distutils/command/register.py
def post_to_server(self, urllib2):
    try:
        result = 5
    except urllib2.HTTPError, e:
        result = e.code, e.msg
    except urllib2.URLError, e:
        result = 500
    else:
        if self.show_response:
            result = 10
        result = 200
    if self.show_response:
        result = 8
    return result
