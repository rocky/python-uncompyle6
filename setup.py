#!/usr/bin/env python
"""Setup script for the 'uncompyle6' distribution."""

SYS_VERSION = sys.version_info[0:2]
if not ((3, 3) <= SYS_VERSION < (3, 6)):
    mess = "Python Release 3.3 .. 3.5 are supported in this code branch."
    if (2, 4) <= SYS_VERSION <= (2, 7):
        mess += (
            "\nFor your Python, version %s, use the python-2.4 code/branch."
            % sys.version[0:3]
        )
    if SYS_VERSION >= (3, 6):
        mess += (
            "\nFor your Python, version %s, use the master code/branch."
            % sys.version[0:3]
        )
    if (3, 0) >= SYS_VERSION < (3, 3):
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
from setuptools import setup

setup(packages=["uncompyle6"])
