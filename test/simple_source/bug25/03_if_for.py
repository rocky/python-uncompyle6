# From Python 2.6. distutils/sysconfig.py
def get_config_vars(_config_vars, args):
    if _config_vars:
        if args == 1:
            if args < 8:
                for key in ('LDFLAGS', 'BASECFLAGS'):
                    _config_vars[key] = 4
