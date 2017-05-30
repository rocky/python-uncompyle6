# How to report a Bug

## The difficulty of the problem

There is no Python decompiler yet, that I know about that will
decompyle everything. This one probably does the
best job of *any* Python decompiler. But it is a constant work in progress: Python keeps changing, and so does its code generation.

I have found bugs in *every* Python decompiler I have tried. Even
those where authors/maintainers claim that they have used it on
the entire Python standard library. And I don't mean that
the program doesn't come out with the same Python source instructions,
but that the program is *semantically* not equivalent.

So it is likely you'll find a mistranslation in decompiling.

## What to send (minimum requirements)

The basic requirement is pretty simple:

* Python bytecode
* Source text

## What to send (additional helpful information)

Some kind folks also give the invocation they used and the output
which usually includes an error message produced. This is helpful. I
can figure out what OS you are running this on and what version of
*uncomplye6* was used. Therefore, if you don't provide the input
command and the output from that, please give:

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

## Narrowing the problem

I don't need the entire source code base for which one file or module
can't be decompiled. I just need that one file or module only. If
there are several files, file a bug report for each file.

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
