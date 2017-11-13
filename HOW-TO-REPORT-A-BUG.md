# How to report a Bug

## The difficulty of the problem

This decompiler is a constant work in progress: Python keeps
changing, and so does its code generation.

There is no Python decompiler yet that I know about that will
decompile everything. Overall, I think this one probably does the best
job of *any* Python decompiler that handles such a wide range of
versions.

But at any given time, there are maybe dozens of valid Python bytecode
files that I know of that will cause problems. And when I get through
those and all the issues of decompiler bugs that are currently logged,
I could probably easily find dozens more bugs just by doing a
decompile of all the Python bytecode on any one of my
computers. Unless you want to help out by _fixing_ bugs, or are
willing to do work by isolating and narrowing bugs, don't feel you are
doing me a favor by doing scans on your favorite sets of bytecode
files.

In sum, it is not uncommon that you will find a mistranslation in
decompiling. Furthermore, you may be expected to do some work in order
to have your bug worthy of being considered above other bugs.

No one is getting paid to work to work on this project, let alone bugs
you may have an interest in. If you require decompiling bytecode
immediately, consider using a decompilation service.

## Is it really a bug?


### Do you have valid bytecode?

As mentioned in README.rst, this project doesn't handle obfuscated
code. See README.rst for suggestions for how to remove some kinds of
obfuscation.

Checking if bytecode is valid is pretty simple: disassemble the code.
Python comes with a disassembly module called `dis`. A prerequisite
module for this package, `xdis` has a cross-python version
disassembler.

### Semantic equivalence vs. exact source code

Almost all versions of Python can perform some sort of code
improvement that can't be undone. In earlier versions of Python it is
rare; in later Python versions, it is more common.

If the code emitted is semantically equivalent, then this isn't a bug.


For example the code might be

```
if a:
  if b:
     x = 1
```

and we might produce:

```
if a and b:
  x = 1
```

These are equivalent. Sometimes

```
else:
   if ...

```

may out as `elif`.


As mentioned in the README. It is possible that Python changes what
you write to be more efficient. For example, for:


```
if True:
  x = 5
```

Python will generate code like:

```
x = 5
```

So just because the text isn't the same, does not
necessarily mean there's a bug.

## What to send (minimum requirements)

The basic requirement is pretty simple:

* Python bytecode
* Python source text

Please don't put files on download services that one has to register
for or can't get to by issuing a simple `curl` or `wget`. If you can't
attach it to the issue, or create a github gist, then the code you are
sending is too large.

Also try to narrow the bug. See below.

## What to send (additional helpful information)

Some kind folks also give the invocation they used and the output
which usually includes an error message produced. This is
helpful. From this, I can figure out what OS you are running this on
and what version of *uncomplye6* was used. Therefore, if you don't
provide the input command and the output from that, please give:

* _uncompyle6_ version used
* OS that you used this on
* Python interpreter version used


### But I don't *have* the source code!

Sure, I get it. No problem. There is Python assembly code on parse
errors, so simply by hand decompile that. To get a full disassembly,
use pydisasm from the [xdis](https://pypi.python.org/pypi/xdis)
package. Opcodes are described in the documentation for
the [dis](https://docs.python.org/3.6/library/dis.html) module.

### But I don't *have* the source code and am incapable of figuring how how to do a hand disassembly!

Well, you could learn. No one is born into this world knowing how to
disassemble Python bytecode. And as Richard Feynman once said, "What
one fool can learn, so can another."

If this is too difficult, or too time consuming, or not of interest to
you, then perhaps what require is a decompilation service. [Crazy
Compilers](http://www.crazy-compilers.com/decompyle/) offers a
byte-code decompiler service for versions of Python up to 2.6. (If
there are others around let me know and I'll list them here.)

## Narrowing the problem

I don't need or want the entire source code base for which one file or
module can't be decompiled. I just need those file(s) or module(s).
If there are several files, file a bug report for each file.

Python modules can get quite large, and usually decompilation problems
occur in a single function or maybe the main-line code but not any of
the functions or classes. So please chop down the source code by
removing those parts that do to decompile properly.

By doing this, you'll probably have a better sense of what exactly is
the problem. Perhaps you can find the boundary of what decompiles, and
what doesn't. That is useful. Or maybe the same file will decompile
properly on a neighboring version of Python. That is helpful too.

In sum, the more you can isolate or narrow the problem, the more
likley the problem will be fixed and fixed sooner.

## Confidentiality of Bug Reports

When you report a bug, you are giving up confidentiality to the source
code and the byte code. However, I would imagine that if you have
narrowed the problem sufficiently, confidentiality little that
remains would not be an issue.

However feel free to remove any commments, and modify variable names
or constants in the source code.
