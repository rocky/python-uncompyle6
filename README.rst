uncompyle6
==========

A Python Byte-code Disassembler and Decompiler


Introduction
------------

A Python 2.x and 3.x byte-code decompiler.
*uncompyle6* translates Python byte-code back into equivalent Python
source code. It accepts byte-codes from Python version 2.5 to 2.7, and
runs on Python 2.6 and 2.7 and Python 3.4.

The generated source is fairly readable: docstrings, lists, tuples and
hashes are somewhat pretty-printed.

*uncompyle6* is based on John Aycock's generic small languages
compiler 'spark' (http://www.csr.uvic.ca/~aycock/python/) and his
prior work on a tool called 'decompyle'. This was improved by Hartmut Goebel
`http://www.crazy-compilers.com/`_

# Additional note (3 July 2004):

This software is no longer available from the original website.
However http://www.crazy-compilers.com/decompyle/ provides a
decompilation service.

# Additional note (5 June 2012):

The decompilation of python bytecode 2.5 & 2.6 is based on the work of
Eloi Vanderbeken. bytecode is translated to a pseudo 2.7 python bytecode
and then decompiled.

# Additional note (12 Dec 2016):

I will be using this to deparse fragments of code inside my trepan_
debuggers_. For that, I need to record text fragements for all
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

::

   make check-2.7 # if running on Python 2.7
   make check-3.4 # if running on Pyton 3.4

Testing right now is largely via utility `test/test_pythonlib.py`.  A
GNU makefile has been added to smooth over setting running the right
command. If you have remake_ installed, you can see the list of all
tasks including tests via `remake --tasks`


Usage
-----

Run

::

     ./bin/uncompyle6 -h
     ./bin/pydisassemble -y

for usage help


Known Bugs/Restrictions
-----------------------

Support Python 3 bytecode and syntax is lacking.

See Also
--------

https://github.com/zrax/pycdc


.. _trepan: https://pypi.python.org/pypi/trepan
.. _debuggers: https://pypi.python.org/pypi/trepan3k
.. _remake: https://bashdb.sf.net/remake
.. _pycdc: https://github.com/zrax/pycdc
