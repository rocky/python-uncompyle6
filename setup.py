#!/usr/bin/env python
"""Setup script for the 'uncompyle6' distribution."""

import sys

SYS_VERSION = sys.version_info[0:2]
if not ((2, 4) <= SYS_VERSION  <= (2, 7)):
    mess = "Python Release 2.4 .. 2.7 are supported in this code branch."
    if ((3, 2) <= SYS_VERSION  <= (3, 7)):
        mess += ("\nFor your Python, version %s, use the master code/branch." %
                 sys.version[0:3])
    else:
        mess += ("\nThis package is not supported before Python 2.4. Your Python version is %s."
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
