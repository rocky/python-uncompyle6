|buildstatus|  |Pypi Installs| |Latest Version| |Supported Python Versions|

|packagestatus|

.. contents::

uncompyle6
==========

A native Python cross-version decompiler and fragment decompiler.
The successor to decompyle, uncompyle, and uncompyle2.

I gave a talk on this at `BlackHat Asia 2024 <https://youtu.be/H-7ZNrpsV50?si=nOaixgYHr7RbILVS>`_.

Introduction
------------

*uncompyle6* translates Python bytecode back into equivalent Python
source code. It accepts bytecodes from Python version 1.0 to version
3.8, spanning over 24 years of Python releases. We include Dropbox's
Python 2.5 bytecode and some PyPy bytecodes.

Why this?
---------

Ok, I'll say it: this software is amazing. It is more than your
normal hacky decompiler. Using compiler_ technology, the program
creates a parse tree of the program from the instructions; nodes at
the upper levels that look a little like what might come from a Python
AST. So we can really classify and understand what's going on in
sections of Python bytecode.

Building on this, another thing that makes this different from other
CPython bytecode decompilers can deparse just
*fragments* of source code and give source-code information around a given bytecode offset.

I use the tree fragments to deparse fragments of code *at run time*
inside my trepan_ debuggers_. For that, bytecode offsets are recorded
and associated with fragments of the source code. This purpose,
although compatible with the original intention, is yet a little bit
different.  See this_ for more information.

Python fragment deparsing, given an instruction offset, is useful in
showing stack traces and can be incorporated into any program that
wants to show a location in more detail than just a line number at
runtime.  This code can also be used when source code information does
not exist and there is just bytecode. Again, my debuggers make use of
this.

There were (and still are) several decompyle, uncompyle,
uncompyle2, uncompyle3 forks around. Many of them come basically from
the same code base, and (almost?) all of them are no longer actively
maintained. One was really good at decompiling Python 1.5-2.3, another is really good at Python 2.7,
but only that. Another handles Python 3.2
only; another patched that and handled only 3.3.  You get the
idea. This code pulls all of these forks together and *moves
forward*. There is some serious refactoring and cleanup in this code
base over those old forks. Even more experimental refactoring is going
on in decompyle3_.

This demonstrably does the best in decompiling Python across all
Python versions. And even when there is another project that only
provides decompilation for a subset of Python versions, we generally do
demonstrably better for those as well.

How can we tell? By taking Python bytecode that comes distributed with
that version of Python and decompiling it.  Among those that
successfully decompile, we can then make sure the resulting programs
are syntactically correct by running the Python interpreter for that
bytecode version.  Finally, in cases where the program has a test for
itself, we can run the check on the decompiled code.

We use automated processes to find bugs. In the issue trackers for
other decompilers, you will find several bugs we've found along
the way. Very few of them are fixed in the other decompilers.

Requirements
------------

The code in the git repository can be run from Python 2.4 to the
latest Python version, except Python 3.0 through
3.2. Volunteers are welcome to address these deficiencies if there is a
desire to do so.

The way it does this, though, is by segregating consecutive Python versions into
git branches:

master
<<<<<<< Updated upstream
   Python 3.11 and up
python-3.6-to-3.10
   Python 3.6 to python-3.10 (uses type annotations)
=======
   Python 3.11 and up (uses poetry install, and newer Python idioms)
python-3.6-to-3.10
   Python 3.6 through 3.10 (uses newer f-strings, and more modern, and more modern Type annotations)
>>>>>>> Stashed changes
python-3.3-to-3.5
   Python 3.3 through 3.5 (Generic Python 3)
python-3.3-to-3.5
   Python 3.3 through 3.5 (Generic Python 3)
python-2.4-to-2.7
   Python 2.4 through 2.7 (Generic Python 2)

PyPy 3-2.4 and later works as well.

The bytecode files it can read have been tested on Python
bytecodes from versions 1.4, 2.1-2.7, and 3.0-3.8 and later PyPy
versions.

Installation
------------

*For recent Python releases (Python 3.11+)*, you can install from PyPI using the name ``uncompyle6``::

    pip install uncompyle6

*For Python releases before 3.11*, do not install using PyPI, but instead install using a file in the [GitHub Releases section](https://github.com/rocky/python-uncompyle6/releases). Older Python used to use `easy_install <https://python101.pythonlibrary.org/chapter29_pip.html#using-easy-install>`_. But this is no longer supported in PyPi.

If the Python version you are running uncompyle6 is between Python 2.4 through 2.7, use a tarball called uncompyle6_24-*x.y.z*.tar.gz.

If the Python version you are running uncompyle6 is between Python 3.0 through 3.2, use a tarball called uncompyle6_30-*x.y.z*.tar.gz.

If the Python version you are running uncompyle6 is between Python 3.3 through 3.5, use a tarball called uncompyle6_33-*x.y.z*.tar.gz.

If the Python version you are running uncompyle6 is between Python 3.6 through 3.11, use a tarball called uncompyle6_36-*x.y.z*.tar.gz.

If the Python version you are running uncompyle6 is 3.11 or later, use a called uncompyle6-*x.y.z*.tar.gz.

You can also try eggs or wheel that have the same version designation, e.g., uncompyle6-*x.y.z*-py39-non-any.whl for a Python 3.9 installation. *However, note that *the version without the designation, means Python 3.11 or greater*.

Similarly a tarball with without `_`*xx* works only from Python 3.11 or greaters


Rationale for using Git Branches
++++++++++++++++++++++++++++++++

It is currently impossible (if not impractical) to have one Python source code of this complexity and with this many features that can run both Python 2.7 and Python 3.13+. The languages have drifted so much, and Packing is vastly different. In fact, the packaging practice for Python 3.11+ is incompatible with Python 2.7 (and before back to Python 2.4), which favored "easy_install".

Installation from source text
++++++++++++++++++++++++++++++

To install from source code make sure you have the right github
branch. See the Requirements section for the Git branch names.

After setting the right branch:

    $ pip install -e .  # set up to run from source tree


A GNU Makefile is also provided, so :code:`make install` (possibly as root or
sudo) will do the steps above.

Running Tests
-------------

::

   make check

A GNU makefile has been added to smooth over setting up and running the right
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

Verification
------------

In older versions of Python, it was possible to verify bytecode by
decompiling it and then compiling using the Python interpreter
for that bytecode version. Having done this, the bytecode produced
could be compared with the original bytecode. However, as Python's code
generation got better, this was no longer feasible.

If you want Python syntax verification of the correctness of the
decompilation process, add the :code:`--syntax-verify` option. However since
Python syntax changes. You should use this option if the bytecode is
the right bytecode for the Python interpreter that will be checking
the syntax.

You can also cross-compare the results with another version of
*uncompyle6* since there are sometimes regressions in decompiling specific bytecode, as the overall quality improves.

For Python 3.7 and 3.8, the code in decompyle3_ is generally
better.

Or try another specific Python decompiler like uncompyle2_, unpyc37_,
or pycdc_.  Since the latter two work differently, bugs here often
aren't in that, and vice versa.

There is an interesting class of these programs that is readily
available to give stronger verification: those programs that, when run,
test themselves. Our test suite includes these.

And Python comes with another set of programs like this: its test
suite for the standard library. We have some code in :code:`test/stdlib` to
facilitate this kind of checking too.

Known Bugs/Restrictions
-----------------------

The biggest known and possibly fixable (but hard) problem has to do with handling control flow. (Python has probably the most diverse and
screwy set of compound statements I've ever seen; there
are "else" clauses on loops and try blocks that I suspect many
programmers don't know about.)

All of the Python decompilers that I have looked at have problems
decompiling Python's control flow. In some cases, we can detect an
erroneous decompilation and report that.

Python support is pretty good for Python 2

On the lower end of Python versions, decompilation seems pretty good, although
we don't have any automated testing in place for Python's distributed tests.
Also, we don't have a Python interpreter for versions 1.6 and 2.0.

In the Python 3 series, Python support is strongest around 3.4 or
3.3 and drops off as you move further away from those versions. Python
3.0 is weird in that it, in some ways, resembles 2.6 more than it does
3.1 or 2.7. Python 3.6 changes things drastically by using word codes
rather than byte codes. As a result, the jump offset field in a jump
instruction argument has been reduced. This makes the :code:`EXTENDED_ARG` instructions now more prevalent in jump instructions; previously
they had been rare.  Perhaps to compensate for the additional
:code:`EXTENDED_ARG` instructions, additional jump optimization has been
added. So in sum handling control flow by ad hoc means, as is currently
done is worse.

Between Python 3.5, 3.6, 3.7, there have been major changes to the
:code:`MAKE_FUNCTION` and :code:`CALL_FUNCTION` instructions.

Python 3.8 removes :code:`SETUP_LOOP`, :code:`SETUP_EXCEPT`,
:code:`BREAK_LOOP`, and :code:`CONTINUE_LOOP`, instructions which may
make control-flow detection harder, lacking the more sophisticated
control-flow analysis that is planned. We'll see.

Currently, not all Python magic numbers are supported. Specifically in
some versions of Python, notably Python 3.6, the magic number has
changes several times within a version.

**We support only released versions, not candidate versions.** Note, however, that the magic of a released version is usually the same as
the *last* candidate version prior to release.

There are also customized Python interpreters, notably Dropbox,
which use their own magic and encrypt bytecode. With the exception of
Dropbox's old Python 2.5 interpreter, this kind of thing is not
handled.

We also don't handle PJOrion_ or otherwise obfuscated code. For
PJOrion try: PJOrion Deobfuscator_ to unscramble the bytecode to get
valid bytecode before trying this tool; pydecipher_ might help with that.

This program can't decompile Microsoft Windows EXE files created by
Py2EXE_, although we can probably decompile the code after you extract
the bytecode properly. `Pydeinstaller <https://github.com/charles-dyfis-net/pydeinstaller>`_ may help with unpacking Pyinstaller bundlers.

Handling pathologically long lists of expressions or statements is
slow. We don't handle Cython_ or MicroPython, which don't use bytecode.

There are numerous bugs in decompilation. And that's true for every
other CPython decompilers I have encountered, even the ones that
claimed to be "perfect" on some particular version like 2.4.

As Python progresses, decompilation also gets harder because the
compilation is more sophisticated and the language itself is more
sophisticated. I suspect that attempts there will be fewer ad-hoc
attempts like unpyc37_ (which is based on a 3.3 decompiler) simply
because it is harder to do so. The good news, at least from my
standpoint, is that I think I understand what's needed to address the
problems in a more robust way. But right now, until such time as
the project is better funded, I do not intend to make any serious effort
to support Python versions 3.8 or 3.9, including bugs that might come
in. I imagine at some point I may be interested in it.

You can easily find bugs by running the tests against the standard
test suite that Python uses to check itself. At any given time, there are
dozens of known problems that are pretty well isolated and that could
be solved if one were to put in the time to do so. The problem is that
there aren't that many people who have been working on bug fixing.

Some of the bugs in 3.7 and 3.8 are simply a matter of back-porting
the fixes in *decompyle3*. Any volunteers?

You may run across a bug that you want to report. Please do so after
reading `How to report a bug
<https://github.com/rocky/python-uncompyle6/blob/master/HOW-TO-REPORT-A-BUG.md>`_ and
follow the `instructions when opening an issue <https://github.com/rocky/python-uncompyle6/issues/new?assignees=&labels=&template=bug-report.md>`_.

Be aware that it might not get my attention for a while. If you
sponsor or support the project in some way, I'll prioritize your
issues above the queue of other things I might be doing instead. In
rare situations, I can do a hand decompilation of bytecode for a fee.
<<<<<<< Updated upstream
However, this is expensive, usually beyond what most people are willing
=======
However this is expansive, usually beyond what most people are willing
>>>>>>> Stashed changes
to spend.

See Also
--------

* https://rocky.github.io/blackhat-asia-2024-additional/all-notes-print.html :  How to Read and Write a High-Level Bytecode Decompiler: ``uncompyle6`` ``decompyle3`` -- BlackHat 2024 Asia (`video <https://www.youtube.com/watch?v=NA77SFncppE>`_. A big thanks to the Organizers and Reviewers for letting me speak. This kind of thing encourages me to work on projects like this.
* https://github.com/rocky/python-decompile3 : Much smaller and more modern code, focusing on 3.7 and 3.8. Changes in that will get migrated back here.
* https://code.google.com/archive/p/unpyc3/ : supports Python 3.2 only. The above projects use a different decompiling technique than what is used here. Currently unmaintained.
* https://github.com/figment/unpyc3/ : fork of above, but supports Python 3.3 only. Includes some fixes like supporting function annotations. Currently unmaintained.
* https://github.com/wibiti/uncompyle2 : supports Python 2.7 only, but does that fairly well. There are situations where :code:`uncompyle6` results are incorrect, while :code:`uncompyle2` results are not, but more often uncompyle6 is correct when uncompyle2 is not. Because :code:`uncompyle6` adheres to accuracy over idiomatic Python, :code:`uncompyle2` can produce more natural-looking code when it is correct. Currently:code:`uncompyle2` is lightly maintained. See its issue `tracker <https://github.com/wibiti/uncompyle2/issues>`_ for more details.
* `How to report a bug <https://github.com/rocky/python-uncompyle6/blob/master/HOW-TO-REPORT-A-BUG.md>`_
* The HISTORY_ file.
* https://github.com/rocky/python-xdis : Cross Python version disassembler
* https://github.com/rocky/python-xasm : Cross Python version assembler
* https://github.com/rocky/python-uncompyle6/wiki : Wiki Documents that describe the code and aspects of it in more detail
* https://github.com/zrax/pycdc : The README for this C++ code says it aims to support all versions of Python. You can aim your slingshot for the moon, too, but I doubt you are going to hit it. This code is best for Python versions around 2.7 and 3.3, when the code was initially developed. Accuracy for current versions of Python 3 and early versions of Python is lacking. Without major effort, it is unlikely that it can be made to support the current Python 3. See its `issue tracker <https://github.com/zrax/pycdc/issues>`_ for details. Currently lightly maintained.


.. _Cython: https://en.wikipedia.org/wiki/Cython
.. _trepan: https://pypi.python.org/pypi/trepan3k
.. _compiler: https://github.com/rocky/python-uncompyle6/wiki/How-does-this-code-work%3F
.. _HISTORY: https://github.com/rocky/python-uncompyle6/blob/master/HISTORY.md
.. _report_bug: https://github.com/rocky/python-uncompyle6/blob/master/HOW-TO-REPORT-A-BUG.md
.. _debuggers: https://pypi.python.org/pypi/trepan3k
.. _remake: https://bashdb.sf.net/remake
.. _pycdc: https://github.com/zrax/pycdc
.. _decompyle3: https://github.com/rocky/python-decompile3
.. _uncompyle2: https://github.com/wibiti/uncompyle2
.. _unpyc37: https://github.com/andrew-tavera/unpyc37
.. _this: https://github.com/rocky/python-uncompyle6/wiki/Deparsing-technology-and-its-use-in-exact-location-reporting
.. |buildstatus| image:: https://circleci.com/gh/rocky/python-uncompyle6.svg?style=svg
		 :target: https://app.circleci.com/pipelines/github/rocky/python-uncompyle6
.. |packagestatus| image:: https://repology.org/badge/vertical-allrepos/python:uncompyle6.svg
		 :target: https://repology.org/project/python:uncompyle6/versions
.. _PJOrion: http://www.koreanrandom.com/forum/topic/15280-pjorion-%D1%80%D0%B5%D0%B4%D0%B0%D0%BA%D1%82%D0%B8%D1%80%D0%BE%D0%B2%D0%B0%D0%BD%D0%B8%D0%B5-%D0%BA%D0%BE%D0%BC%D0%BF%D0%B8%D0%BB%D1%8F%D1%86%D0%B8%D1%8F-%D0%B4%D0%B5%D0%BA%D0%BE%D0%BC%D0%BF%D0%B8%D0%BB%D1%8F%D1%86%D0%B8%D1%8F-%D0%BE%D0%B1%D1%84
.. _pydecipher: https://github.com/mitre/pydecipher
.. _Deobfuscator: https://github.com/extremecoders-re/PjOrion-Deobfuscator
.. _Py2EXE: https://en.wikipedia.org/wiki/Py2exe
.. |Supported Python Versions| image:: https://img.shields.io/pypi/pyversions/uncompyle6.svg
.. |Latest Version| image:: https://badge.fury.io/py/uncompyle6.svg
		 :target: https://badge.fury.io/py/uncompyle6
.. |Pypi Installs| image:: https://pepy.tech/badge/uncompyle6/month
