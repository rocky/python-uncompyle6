#!/usr/bin/env python

"""Setup script for the 'uncompyle6' distribution."""

from __pkginfo__ import \
    author,           author_email,                                  \
    license,          long_description,                              \
    modname,          packages,           py_modules,       scripts, \
    short_desc,       web,                zip_safe

__import__('pkg_resources')
from setuptools import setup

exec(open('uncompyle6/version.py').read())

setup(
       author             = author,
       author_email       = author_email,
       # classifiers        = classifiers,
       description        = short_desc,
       # install_requires   = install_requires,
       license            = license,
       long_description   = long_description,
       py_modules         = py_modules,
       name               = modname,
       packages           = packages,
       test_suite         = 'nose.collector',
       url                = web,
       setup_requires     = ['nose>=1.0'],
       scripts            = scripts,
       version            = VERSION,
       zip_safe           = zip_safe)
