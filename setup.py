#!/usr/bin/env python

"""Setup script for the 'uncompyle6' distribution."""

# Get the package information used in setup().
# from __pkginfo__ import \
#     author,           author_email,       classifiers,                    \
#     install_requires, license,            long_description,               \
#     modname,          packages,           py_modules,   \
#     short_desc,       version,            web,              zip_safe

from __pkginfo__ import \
    author,           author_email,                                  \
    long_description,                                                \
    modname,          packages,           py_modules,       scripts, \
    short_desc,       version,            web,              zip_safe

__import__('pkg_resources')
from setuptools import setup

setup(
       author             = author,
       author_email       = author_email,
       # classifiers        = classifiers,
       description        = short_desc,
       # install_requires   = install_requires,
       # license            = license,
       long_description   = long_description,
       py_modules         = py_modules,
       name               = modname,
       packages           = packages,
       test_suite         = 'nose.collector',
       url                = web,
       setup_requires     = ['nose>=1.0'],
       scripts            = scripts,
       version            = version,
       zip_safe           = zip_safe)
