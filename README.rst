uncompyle2 
==========

A Python 2.5, 2.6, 2.7 byte-code decompiler, written in Python 2.7

Introduction
------------

'uncompyle2' converts Python byte-code back into equivalent Python
source code. It accepts byte-code from Python version 2.5 to 2.7. 
Additionally, it will only run on Python 2.7.

The generated source is very readable: docstrings, lists, tuples and
hashes get pretty-printed.

'uncompyle2' is based on John Aycock's generic small languages compiler
'spark' (http://www.csr.uvic.ca/~aycock/python/) and his prior work on
a tool called 'decompyle'. This tool has been vastly improved by
Hartmut Goebel `http://www.crazy-compilers.com/`_

# Additional note (3 July 2004, Ben Burton):

This software is no longer available from the original website. It has
now become a commercial decompilation service, with no software
available for download.

Any developers seeking to make alterations or enhancements to this code
should therefore consider these debian packages an appropriate starting
point.

# Additional note (5 June 2012):

The decompilation of python bytecode 2.5 & 2.6 is based on the work of
Eloi Vanderbeken. bytecode is translated to a pseudo 2.7 python bytecode
and then decompiled.

Features
--------

- decompiles Python byte-code into equivalent Python source
- decompiles byte-code from Python version 2.5, 2.6, 2.7
- pretty-prints docstrings, hashes, lists and tuples
- reads directly from .pyc/.pyo files, bulk-decompile whole directories
- output may be written to file, a directory or to stdout
- option for including byte-code disassembly into generated source

For a list of changes please refer to the 'CHANGES' file.


Requirements
------------

uncompyle2 requires Python 2.7


Installation
------------

You may either create a RPM and install this, or install directly from
the source distribution.

Creating RPMS:

    python setup.py bdist_rpm

### Installation from the source distribution:

    python setup.py install

To install to a user's home-dir:

    python setup.py install --home=<dir>

To install to another prefix (eg. /usr/local)

    python setup.py install --prefix=/usr/local

For more information on 'Installing Python Modules' please refer to
http://www.python.org/doc/current/inst/inst.html


Usage
-----

./scripts/uncompyle2 -h		prints usage

./test_pythonlib.py		test files and python library

Known Bugs/Restrictions
-----------------------

No support for python 3.2

It currently reconstructs most of Python code but probably needs to be tested more thoroughly. All feedback welcome
