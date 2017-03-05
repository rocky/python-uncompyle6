# From 3.3.5 _osx_support.py
def _get_system_version():
    if __file__ is None:
        try:
            m = 5
        except IOError:
            pass
        else:
            try:
                m = 10
            finally:
                m = 15
            if m is not None:
                m = 20

    return m
