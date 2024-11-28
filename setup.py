#!/usr/bin/env python
"""Setup script for the 'uncompyle6' distribution."""
import sys

import setuptools

SYS_VERSION = sys.version_info[0:2]
if not ((3, 6) <= SYS_VERSION < (3, 11)):
    mess = "Python Release 3.6 .. 3.10 are supported in this code branch."
    if (2, 4) <= SYS_VERSION <= (2, 7):
        mess += (
            "\nFor your Python, version %s, use the python-2.4 code/branch."
            % sys.version[0:3]
        )
    elif SYS_VERSION >= (3, 10):
        mess += (
            "\nFor your Python, version %s, use the master code/branch."
            % sys.version[0:3]
        )
    elif (3, 0) >= SYS_VERSION < (3, 3):
        mess += (
            "\nFor your Python, version %s, use the python-3.0-to-3.2 code/branch."
            % sys.version[0:3]
        )
    elif SYS_VERSION < (2, 4):
        mess += (
            "\nThis package is not supported for Python version %s." % sys.version[0:3]
        )
    print(mess)
    raise Exception(mess)

from __pkginfo__ import (
    __version__,
    author,
    author_email,
    classifiers,
    entry_points,
    install_requires,
    license,
    long_description,
    modname,
    py_modules,
    short_desc,
    web,
    zip_safe,
)

setuptools.setup(
    author=author,
    author_email=author_email,
    classifiers=classifiers,
    description=short_desc,
    entry_points=entry_points,
    install_requires=install_requires,
    license=license,
    long_description=long_description,
    long_description_content_type="text/x-rst",
    name=modname,
    packages=setuptools.find_packages(),
    py_modules=py_modules,
    test_suite="nose.collector",
    url=web,
    version=__version__,
    zip_safe=zip_safe,
)
