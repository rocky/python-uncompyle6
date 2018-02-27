# Bug was found in 3.6 _osx_support.py in if/elif needing
# EXTENDED_ARGS which are the targets of jumps.
def get_platform_osx(_config_vars, osname, release, machine, sys, re):
    """Filter values for get_platform()"""

    macver = _config_vars.get('MACOSX_DEPLOYMENT_TARGET', '')
    macrelease = release or 10
    macver = macver or macrelease

    if macver:
        release = macver
        osname = "macosx"

        cflags = _config_vars.get('CFLAGS', _config_vars.get('CFLAGS', ''))
        if macrelease:
            try:
                macrelease = tuple(int(i) for i in macrelease.split('.')[0:2])
            except ValueError:
                macrelease = (10, 0)
        else:
            macrelease = (10, 0)

        if (macrelease >= (10, 4)) and '-arch' in cflags.strip():
            machine = 'fat'

            archs = re.findall(r'-arch\s+(\S+)', cflags)
            archs = tuple(sorted(set(archs)))

            if len(archs) == 1:
                machine = archs[0]
            elif archs == ('i386', 'ppc'):
                machine = 'fat'
            elif archs == ('i386', 'x86_64'):
                machine = 'intel'
            elif archs == ('i386', 'ppc', 'x86_64'):
                machine = 'fat3'
            elif archs == ('ppc64', 'x86_64'):
                machine = 'fat64'
            elif archs == ('i386', 'ppc', 'ppc64', 'x86_64'):
                machine = 'universal'
            else:
                raise ValueError(
                   "Don't know machine value for archs=%r" % (archs,))

        elif machine == 'i386':
            if sys.maxsize >= 2**32:
                machine = 'x86_64'

    return (osname, release, machine)
