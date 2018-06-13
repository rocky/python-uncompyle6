|buildstatus| |Latest Version| |Supported Python Versions|

uncompyle6
==========

A native Python cross-version decompiler and fragment decompiler.
The successor to decompyle, uncompyle, and uncompyle2.


Introduction
------------

*uncompyle6* translates Python bytecode back into equivalent Python
source code. It accepts bytecodes from Python version 1.3 to version
3.7, spanning over 22 years of Python releases. We include Dropbox's
Python 2.5 bytecode and some PyPy bytecode.

Why this?
---------

Ok, I'll say it: this software is amazing. It is more than your
normal hacky decompiler. Using compiler_ technology, the program
creates a parse tree of the program from the instructions; nodes at
the upper levels that look a little like what might come from a Python
AST. So we can really classify and understand what's going on in
sections of Python bytecode.

Building on this, another thing that makes this different from other
CPython bytecode decompilers is the ability to deparse just
*fragments* of source code and give source-code information around a
given bytecode offset.

I use the tree fragments to deparse fragments of code *at run time*
inside my trepan_ debuggers_. For that, bytecode offsets are recorded
and associated with fragments of the source code. This purpose,
although compatible with the original intention, is yet a little bit
different.  See this_ for more information.

Python fragment deparsing given an instruction offset is useful in
showing stack traces and can be encorporated into any program that
wants to show a location in more detail than just a line number at
runtime.  This code can be also used when source-code information does
not exist and there is just bytecode. Again, my debuggers make use of
this.

There were (and still are) a number of decompyle, uncompyle,
uncompyle2, uncompyle3 forks around. Almost all of them come basically
from the same code base, and (almost?) all of them are no longer
actively maintained. One was really good at decompiling Python 1.5-2.3
or so, another really good at Python 2.7, but that only. Another
handles Python 3.2 only; another patched that and handled only 3.3.
You get the idea. This code pulls all of these forks together and
*moves forward*. There is some serious refactoring and cleanup in this
code base over those old forks.

This demonstrably does the best in decompiling Python across all
Python versions. And even when there is another project that only
provides decompilation for subset of Python versions, we generally do
demonstrably better for those as well.

How can we tell? By taking Python bytecode that comes distributed with
that version of Python and decompiling these.  Among those that
successfully decompile, we can then make sure the resulting programs
are syntactically correct by running the Python interpreter for that
bytecode version.  Finally, in cases where the program has a test for
itself, we can run the check on the decompiled code.

We are serious about testing, and use automated processes to find
bugs. In the issue trackers for other decompilers, you will find a
number of bugs we've found along the way. Very few to none of them are
fixed in the other decompilers.

Requirements
------------

The code here can be run on Python versions 2.6 or later, PyPy 3-2.4,
or PyPy-5.0.1.  Python versions 2.4-2.7 are supported in the
python-2.4 branch.  The bytecode files it can read have been tested on
Python bytecodes from versions 1.4, 2.1-2.7, and 3.0-3.6 and the
above-mentioned PyPy versions.

Installation
------------

This uses setup.py, so it follows the standard Python routine:

::

    pip install -e .  # set up to run from source tree
                      # Or if you want to install instead
    python setup.py install # may need sudo

A GNU makefile is also provided so :code:`make install` (possibly as root or
sudo) will do the steps above.

Testing
-------

::

   make check

A GNU makefile has been added to smooth over setting running the right
command, and running tests from fastest to slowest.

If you have remake_ installed, you can see the list of all tasks
including tests via :code:`remake --tasks`


Usage
-----

Run

::

$ uncompyle6 *compiled-python-file-pyc-or-pyo*

For usage help:

::

   $ uncompyle6 -h

If you want strong verification of the correctness of the
decompilation process, add the `--verify` option. But there are
situations where this will indicate a failure, although the generated
program is semantically equivalent. Using option `--weak-verify` will
tell you if there is something definitely wrong. Generally, large
swaths of code are decompiled correctly, if not the entire program.

You can also cross compare the results with pycdc_ . Since they work
differently, bugs here often aren't in that, and vice versa.


Known Bugs/Restrictions
-----------------------

The biggest known and possibly fixable (but hard) problem has to do
with handling control flow. (Python has probably the most diverse and
screwy set of compound statements I've ever seen; there
are "else" clauses on loops and try blocks that I suspect many
programmers don't know about.)

All of the Python decompilers that I have looked at have problems
decompiling Python's control flow. In some cases we can detect an
erroneous decompilation and report that.

In older versions of Python it was possible to verify bytecode by
decompiling bytecode, and then compiling using the Python interpreter
for that bytecode version. Having done this the bytecode produced
could be compared with the original bytecode. However as Python's code
generation got better, this is no longer feasible.

There verification that we use that doesn't check bytecode for
equivalence but does check to see if the resulting decompiled source
is a valid Python program by running the Python interpreter. Because
the Python language has changed so much, for best results you should
use the same Python version in checking as was used in creating the
bytecode.

There are however an interesting class of these programs that is
readily available give stronger verification: those programs that
when run check some computation, or even better themselves.

And already Python has a set of programs like this: the test suite
for the standard library that comes with Python. We have some
code in `test/stdlib` to facilitate this kind of checking.

Python support is strongest in Python 2 for 2.7 and drops off as you
get further away from that. Support is also probably pretty good for
python 2.3-2.4 since a lot of the goodness of early the version of the
decompiler from that era has been preserved (and Python compilation in
that era was minimal)

There is some work to do on the lower end Python versions which is
more difficult for us to handle since we don't have a Python
interpreter for versions 1.6, and 2.0.

In the Python 3 series, Python support is is strongest around 3.4 or
3.3 and drops off as you move further away from those versions. Python
3.0 is weird in that it in some ways resembles 2.6 more than it does
3.1 or 2.7. Python 3.6 changes things drastically by using word codes
rather than byte codes. As a result, the jump offset field in a jump
instruction argument has been reduced. This makes the `EXTENDED_ARG`
instructions are now more prevalent in jump instruction; previously
they had been rare.  Perhaps to compensate for the additional
`EXTENDED_ARG` instructions, additional jump optimization has been
added. So in sum handling control flow by ad hoc means as is currently
done is worse.

Between Python 3.5, 3.6 and 3.7 there have been major changes to the
`MAKE_FUNCTION` and `CALL_FUNCTION` instructions.

Currently not all Python magic numbers are supported. Specifically in
some versions of Python, notably Python 3.6, the magic number has
changes several times within a version. We support only the released
magic. There are also customized Python interpreters, notably Dropbox,
which use their own magic and encrypt bytcode. With the exception of
the Dropbox's old Python 2.5 interpreter this kind of thing is not
handled.

We also don't handle PJOrion_ obfuscated code. For that try: PJOrion
Deobfuscator_ to unscramble the bytecode to get valid bytecode before
trying this tool. This program can't decompile Microsoft Windows EXE
files created by Py2EXE_, although we can probably decompile the code
after you extract the bytecode properly. For situations like this, you
might want to consider a decompilation service like `Crazy Compilers
<http://www.crazy-compilers.com/decompyle/>`_.  Handling
pathologically long lists of expressions or statements is slow.


There is lots to do, so please dig in and help.

See Also
--------

* https://github.com/zrax/pycdc : purports to support all versions of Python. It is written in C++ and is most accurate for Python versions around 2.7 and 3.3 when the code was more actively developed. Accuracy for more recent versions of Python 3 and early versions of Python are especially lacking. See its `issue tracker <https://github.com/zrax/pycdc/issues>`_ for details. Currently lightly maintained.
* https://code.google.com/archive/p/unpyc3/ : supports Python 3.2 only. The above projects use a different decompiling technique than what is used here. Currently unmaintained.
* https://github.com/figment/unpyc3/ : fork of above, but supports Python 3.3 only. Includes some fixes like supporting function annotations. Currently unmaintained.
* https://github.com/wibiti/uncompyle2 : supports Python 2.7 only, but does that fairly well. There are situtations where `uncompyle6` results are incorrect while `uncompyle2` results are not, but more often uncompyle6 is correct when uncompyle2 is not. Because `uncompyle6` adheres to accuracy over idiomatic Python, `uncompyle2` can produce more natural-looking code when it is correct. Currently `uncompyle2` is lightly maintained. See its issue `tracker <https://github.com/wibiti/uncompyle2/issues>`_ for more details
* `How to report a bug <https://github.com/rocky/python-uncompyle6/blob/master/HOW-TO-REPORT-A-BUG.md>`_
* The HISTORY_ file.
* https://github.com/rocky/python-xdis : Cross Python version disassembler
* https://github.com/rocky/python-xasm : Cross Python version assembler
* https://github.com/rocky/python-uncompyle6/wiki : Wiki Documents which describe the code and aspects of it in more detail


.. _trepan: https://pypi.python.org/pypi/trepan2
.. _compiler: https://pypi.python.org/pypi/spark_parser
.. _HISTORY: https://github.com/rocky/python-uncompyle6/blob/master/HISTORY.md
.. _debuggers: https://pypi.python.org/pypi/trepan3k
.. _remake: https://bashdb.sf.net/remake
.. _pycdc: https://github.com/zrax/pycdc
.. _this: https://github.com/rocky/python-uncompyle6/wiki/Deparsing-technology-and-its-use-in-exact-location-reporting
.. |buildstatus| image:: https://travis-ci.org/rocky/python-uncompyle6.svg
		 :target: https://travis-ci.org/rocky/python-uncompyle6
.. _PJOrion: http://www.koreanrandom.com/forum/topic/15280-pjorion-%D1%80%D0%B5%D0%B4%D0%B0%D0%BA%D1%82%D0%B8%D1%80%D0%BE%D0%B2%D0%B0%D0%BD%D0%B8%D0%B5-%D0%BA%D0%BE%D0%BC%D0%BF%D0%B8%D0%BB%D1%8F%D1%86%D0%B8%D1%8F-%D0%B4%D0%B5%D0%BA%D0%BE%D0%BC%D0%BF%D0%B8%D0%BB%D1%8F%D1%86%D0%B8%D1%8F-%D0%BE%D0%B1%D1%84
.. _Deobfuscator: https://github.com/extremecoders-re/PjOrion-Deobfuscator
.. _Py2EXE: https://en.wikipedia.org/wiki/Py2exe
.. |Supported Python Versions| image:: https://img.shields.io/pypi/pyversions/uncompyle6.svg
.. |Latest Version| image:: https://badge.fury.io/py/uncompyle6.svg
		 :target: https://badge.fury.io/py/uncompyle6
