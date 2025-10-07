#!/usr/bin/env python
"""Setup script for the 'uncompyle6' distribution.
  Note: that we use 2.x compatible Python code here.
"""
import sys

import setuptools

major = sys.version_info[0]
minor = sys.version_info[1]
SYS_VERSION = sys.version_info[0:2]
if not ((3, 3) <= SYS_VERSION < (3, 6)):
    sys.stderr.write("Python Release 3.3 .. 3.5 are supported in this code branch. You are running Python %s.%s.\n" % (major, minor))
    if (2, 4) <= SYS_VERSION <= (2, 7):
        sys.stderr.write("Please install using uncompyle6_24-x.y.z.tar.gz from https://github.com/rocky/python-uncompyle6/releases\n")
        sys.stderr.write("Or to install from source, use the python-2.4-to-2.7 code/branch.\n")
        sys.exit(1)
    elif SYS_VERSION >= (3, 10):
        sys.stderr.write("Please install using uncompyle6-x.y.z.tar.gz from https://github.com/rocky/python-uncompyle6/releases\n")
        sys.stderr.write("Or to install from source, use the master code/branch.\n")
        sys.exit(1)
    elif (3, 0) >= SYS_VERSION < (3, 3):
        sys.stderr.write("Please install using uncompyle6_30-x.y.z.tar.gz from https://github.com/rocky/python-uncompyle6/releases\n")
        sys.stderr.write("Or to install from source, use the python-3.0-to-3.2 code/branch.\n")
        sys.exit(1)
    elif (3, 6) >= SYS_VERSION < (3, 10):
        sys.stderr.write("Please install using uncompyle6_36-x.y.z.tar.gz from https://github.com/rocky/python-uncompyle6/releases\n")
        sys.stderr.write("Or to install from source, use the python-3.3-to-3.5 code/branch.\n")
        sys.exit(1)
    elif SYS_VERSION < (2, 4):
        sys.stderr.write("This package is not supported for Python\n")
        sys.exit(1)
    raise Exception("Wrong Python version")

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
