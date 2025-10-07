"""
  Check that the Python version running this is compatible with this installation medium.
  Note: that we use 2.x compatible Python code here.
"""
import sys
from setuptools import setup

major = sys.version_info[0]
minor = sys.version_info[1]

if major != 3 or not minor >= 11:
    sys.stderr.write("This installation medium is only for Python 3.11 and later. You are running Python %s.%s.\n" % (major, minor))

if major == 3 and 6 <= minor <= 10:
    sys.stderr.write("Please install using uncompyle6_36-x.y.z.tar.gz from https://github.com/rocky/python-uncompyle6/releases\n")
    sys.exit(1)
elif major == 3 and 3 <= minor <= 5:
    sys.stderr.write("Please install using uncompyle6_33-x.y.z.tar.gz from https://github.com/rocky/python-uncompyle6/releases\n")
    sys.exit(1)
if major == 3 and 0 <= minor <= 2:
    sys.stderr.write("Please install using uncompyle6_30-x.y.z.tar.gz from https://github.com/rocky/python-uncompyle6/releases\n")
    sys.exit(1)
elif major == 2:
    sys.stderr.write("Please install using uncompyle6_24-x.y.z.tar.gz from https://github.com/rocky/python-uncompyle6/releases\n")
    sys.exit(1)


setup()
