uncompyle6
==========

A CPython 2.x and possibly 3.x byte-code disassembler and
adecompiler.

This is written in Python 2.7 but is Python3 compatible.


Introduction
------------

'uncompyle6' converts Python byte-code back into equivalent Python
source code. It accepts byte-codes from Python version 2.5 to 2.7.
It runs on Python 2.7 and, with a little more work, on Python 3 as well.

The generated source is fairly readable: docstrings, lists, tuples and
hashes are somewhat pretty-printed.

'uncompyle6' is based on John Aycock's generic small languages
compiler 'spark' (http://pages.cpsc.ucalgary.ca/~aycock/spark/) and his
prior work on a tool called 'decompyle'. This was improved by Hartmut Goebel
http://www.crazy-compilers.com

In order to the decompile a program, we need to be able to disassemble
it first. And this process may be useful in of itself. So we provide a
utility for just that piece as well.

'pydisassemble' gives a CPython disassembly of Python byte-code. How
is this different than what Python already provides via the "dis"
module?  Here, we can cross disassemble bytecodes from different
versions of CPython than the version of CPython that is doing the
disassembly.

'pydisassemble works on the same versions as 'uncompyle6' and handles the
same sets of CPython bytecode versions.

*Note from 3 July 2004:*

This software was original available from http://www.crazy-compilers.com;
http://www.crazy-compilers.com/decompyle/ provides a decompilation service.

*Note (5 June 2012):*

The decompilation of python bytecode 2.5 & 2.6 is based on the work of
Eloi Vanderbeken. bytecode is translated to a pseudo 2.7 python bytecode
and then decompiled.

*Note (12 Dec 2016):*

This project will be used to deparse fragments of code inside my
trepan_ debuggers_. For that, I need to record text fragements for all
byte-code offsets (of interest). This purpose although largely
compatible with the original intention is yet a little bit different.


Features
--------

- decompiles Python byte-code into equivalent Python source
- decompiles byte-code from Python version 2.5, 2.6, 2.7
- pretty-prints docstrings, hashes, lists and tuples
- reads directly from .pyc/.pyo files, bulk-decompile whole directories
- output may be written to file, a directory or to stdout
- option for including byte-code disassembly into generated source

Requirements
------------

The code runs on Python 2.7. It is compatable with Python3,
and I've run some tests there, but more work is needed to make that
more solid.

Work to support decompyling Python 3 bytecodes and magics is
still needed.


Installation
------------

This uses setup.py, so it follows the standard Python routine:

::

    python setup.py install # may need sudo
    # or if you have pyenv:
    python setup.py develop

A GNU makefile is also provided so `make install` (possibly as root or
sudo) will do the steps above.

Testing
-------

Testing right now is largely via utility `test/test_pythonlib.py`.  A
GNU makefile has been added to smooth over setting running the right
command. If you have remake_ installed, you can see the list of all
tasks including tests via `remake --tasks`


Usage
-----

Run

::

     ./scripts/uncompyle6 -h


for usage help


Known Bugs/Restrictions
-----------------------

Support for Python 3 bytecode and syntax is lacking.

.. _trepan: https://pypi.python.org/pypi/trepan
.. _debuggers: https://pypi.python.org/pypi/trepan3k
.. _remake: https://bashdb.sf.net/remake
