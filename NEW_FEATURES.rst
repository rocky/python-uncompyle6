Introduction
============

The original versions of this code up until the time I started were
pretty awesome.  You can get a sense of this by running it.  For the
most part it was remarkably fast, and a single module with few dependencies.

Here I will largely give what are the major improvements over old code.

This also serves to outline a little bit about what is in this code.

See also `How does this code work? <https://github.com/rocky/python-uncompyle6/wiki/How-does-this-code-work%3F>`_.

Old Cool Features
==================

Before getting to the new stuff, I'll describe cool things that was there before.

I particularly liked the ability to show the assembly, grammar
reduction rules as they occurred, and the resulting parse tree. It is
neat that you could follow the process and steps that deparser takes,
and in this not only see the result how the bytecode corresponds to
the resulting source. Compare this with other Python decompilers.

And of course also neat was that this used a grammar and table-driven
approach to decompile.


Expanding decompilation to multiple Python Versions
==================================================

Aside from ``pycdc``, most of the Python decompilers handle a small
number of Python versions, if they supported more than one. And even
when more than one version is supported if you have to be running the
Python version that the bytecode was compiled for.

There main reason that you have to be running the Python bytecode
interpreter as the one you want to decompile largely stems from the
fact that Python's ``dis`` module is often what is used and that has this limitation.

``pycdc`` doesn't suffer this problem because it is written in C++,
not Python.  Hartmut Goebel's code had provisions for multiple Python
versions running from an interpreter different from the one that was
running the decompiler. That however used compiled code in the process
was tied a bit to the Python C headers for a particular version.

You need to not only to account for different "marshal" and "unmarshal"
routines for the different Python versions, but also, as the Python versions
extend, you need a different code type as well.

Enter ``xdis``
--------------

To handle all of these problems, I split off the marshal loading
portion and disassembly routines into a separate module,
`xdis <https://pypi.org/project/xdis/>`_. This also allows older Pythons to have access to features
found in newer Pythons, such as parsing the bytecode, a uniform stream
of bytes, into a list of structured bytecode instructions.

Python 2.7's ``dis`` module doesn't has provide a instruction abstraction.
Therefore in ``uncompyle2`` and other earlier decompilers you see code with magic numbers like 4 in::

    if end > jump_back+4 and code[end] in (JF, JA):
        if code[jump_back+4] in (JA, JF):
            if self.get_target(jump_back+4) == self.get_target(end):
                self.fixed_jumps[pos] = jump_back+4
                end = jump_back+4
    elif target < pos:
        self.fixed_jumps[pos] = jump_back+4
        end = jump_back+4

and in other code -1 and 3 in::

        if self.get_target(jmp) != start_else:
            end_else = self.get_target(jmp)
        if self.code[jmp] == JF:
            self.fixed_jumps[jmp] = -1
        self.structs.append({'type':  'except',
                       'start': i,
                       'end':   jmp})
        i = jmp + 3

All of that offset arithmetic is trying to find the next instruction
offset or the previous offset. Using a list of instructions you simply
take the ``offset`` field of the previous or next instruction.

The above code appears in the ``uncompyle2`` "Scanner" class in
service of trying to figure out control flow. Note also that there
isn't a single comment in there about what specifically it is trying
to do, the logic or that would lead one to be confident that this is
correct, let alone assumptions that are needed for this to be true.

While this might largely work for Python 2.7, and ``uncompyle2`` does
get control flow wrong sometimes, it is impossible to adapt code for
other versions of Python.

In addition adding an instruction structure, ``xdis`` adds various
flags and features that assist in working with instructions. In the
example above this replaces code like ``... in (JF, JA)`` which is
some sort of unconditional jump instruction.

Although not needed in the decompiler, ``xdis`` also has nicer
instruction print format. It can show you the bytes as well as the
interpreted instructions. It will interpret flag bits and packed
structures in operands so you don't have to. It can even do a limited
form of inspection at previous instructions to give a more complete
description of an operand. For example on ``LOAD_ATTR`` which loads
the attribute of a variable, often the variable name can be found as
the previous instruction. When that is the case the disassembler can
include that in the disassembly display for the ``LOAD_ATTR`` operand.


Python Grammar Isolation
------------------------

If you want to support multiple versions of Python in a manageable way
you really need to provide different grammars for the different
versions, in a grammar-based system. None of the published versions of
this decompiler did this.

If you look at the changes in this code, right now there are no
grammar changes needed between 1.0 to 1.3. (Some of this may be wrong
though since we haven't extensively tested these earliest Python versions

For Python 1.4 which is based off of the grammar for 1.5 though there
are number of changes, about 6 grammar rules. Later versions of though
we start to see larger upheaval and at certain places, especially
those where new opcodes are introduced, especially those that change
the way calls or exceptions get handled, we have major upheaval in the
grammar. It is not just that some rules get added, but we also need to
*remove* some grammar rules as well.

I have been largely managing this as incremental differences between versions.
However in the future I am leaning more towards totally separate grammars.
A well constructed grammar doesn't need to be that large.

When starting out a new version, we can just copy the grammar from the
prior version.  Within a Python version though, I am breaking these
into composable pieces. In particular the grammar for handling what
can appear as the body of a lambda, is a subset of the full Python
language. The language allowed in an ``eval`` is also a subset of the
full Python language, as are what can appear in the various
compilation modes like "single" versus "exec".

Another nice natural self-contain grammar section is what can appear
in list comprehensions and generators. The bodies of these are
generally represented in a self-contained code block.

Often in decompilation you may be interested not just in decompiling
the entire code but you may be interested in only focusing on a
specific part of the code. And if there is a problem in decompiling
the entire piece of code, having these smaller breaking points can be
of assistance.

Other Modularity
----------------

Above we have mentioned the need for separate grammars or to isolate
these per versions. But there are other major pieces that make up this
decompiler. In particular there is a scanner and the source code
generation part.

Even though differences in version that occur in disassembly are
handled by ``xdis``, we still have to do conversion of that to a token
stream for parsing. So the scanners are again broken out per version
with various OO mechanisms for reusing code. The same is true for
source code generation.


Expanding decompiler availability to multiple Python Versions
--------------------------------------------------------------

Above we mention decompiling multiple versions of bytecode from a
single Python interpreter. We talk about having the decompiler
runnable from multiple versions of Python, independent of the set of
bytecode that the decompiler supports.


There are slight advantages in having a decompiler that runs the same
version as the code you are decompiling. The most obvious one is that
it makes it easy to test to see whether the decompilation correct
because you can run the decompiled code. Python comes with a suite of
Python programs that check themselves and that aspects of Python are
implemented correctly. These also make excellent programs to check
whether a program has decompiled correctly.

Aside from this, debugging can be easier as well. To assist
understanding bytecode and single stepping it see `x-python
<https://pypi.org/project/x-python/>`_ and the debugger for it
`trepan-xpy <https://pypi.org/project/trepanxpy/>`_.

Handling Language Drift
-----------------------

Given the desirability of having this code running on logs of Python
versions, how can we get this done?

The solution used here is to have several git branches of the
code. Right now there are 3 branches. Each branch handles works across
3 or so different releases of Python. In particular one branch handles
Python 2.4 to 2.7 Another handles Python 3.3 to 3.5, and the master
branch handles 3.6 to 3.10. (Again note that the 3.9 and 3.10
decompilers do not decompile Python 3.9 or 3.10, but they do handle
bytecode for all earlier versions.)


Cool features of the Parser
===========================

* reduction rule checking
* numbering tokens
* showing a stack of completions

Cool features Semantic Analysis
===============================

* ``--tree++`` (``-T``) option
* showing precedence
* See `Adding a tree transformation phase to uncompyle6 <https://github.com/rocky/python-uncompyle6/wiki/Adding-a-tree-transformation-phase-to-uncompyle6>`_
* following AST
* Fragment deparsing
