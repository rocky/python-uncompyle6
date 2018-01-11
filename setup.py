#!/usr/bin/env python
import sys

"""Setup script for the 'uncompyle6' distribution."""

SYS_VERSION = sys.version_info[0:2]
if not ((2, 6) <= SYS_VERSION  <= (3, 7)) or ((3, 0) <= SYS_VERSION <= (3, 1)):
    mess = "Python Release 2.6 .. 3.7 excluding 3.0 and 3.1 are supported in this code branch."
    if ((2, 4) <= SYS_VERSION <= (2, 7)):
        mess += ("\nFor your Python, version %s, use the python-2.4 code/branch." %
                 sys.version[0:3])
    elif SYS_VERSION < (2, 4) or ((3, 0) <= SYS_VERSION <= (3, 1)):
        mess += ("\nThis package is not supported for Python version %s."
                 % sys.version[0:3])
    print(mess)
    raise Exception(mess)

from __pkginfo__ import \
    author,           author_email,       install_requires,          \
    license,          long_description,   classifiers,               \
    entry_points,     modname,            py_modules,                \
    short_desc,       VERSION,            web,                       \
    zip_safe

from setuptools import setup, find_packages
setup(
       author             = author,
       author_email       = author_email,
       classifiers        = classifiers,
       description        = short_desc,
       entry_points       = entry_points,
       install_requires   = install_requires,
       license            = license,
       long_description   = long_description,
       name               = modname,
       packages           = find_packages(),
       py_modules         = py_modules,
       test_suite         = 'nose.collector',
       url                = web,
       tests_require      = ['nose>=1.0'],
       version            = VERSION,
       zip_safe           = zip_safe)
