---
name: Bug report
about: Tell us about uncompyle6 bugs

---

<!-- __Note:__ If you are using this program to do something illegal - don't.
The issue may be flagged to make it easier for those looking for illegal activity.

If you are reporting a bug in decompilation, it will probably not be acted upon
unless it is narrowed to a small example. You may have to do some work remove
extraneous code from the source example. Most bugs can be expressed in 30 lines of
code.

Issues are not for asking questions about a problem you
are trying to solve that involve the use of uncompyle6 along the way,
although I may be more tolerant of this if you sponsor the project.

Bugs are also not for general or novice kind help on how to install
this Python program and its dependencies in your environment, or in
the way you would like to have it set up, or how to interpret a Python
traceback e.g. that winds up saying Python X.Y.Z is not supported.

For these kinds of things, you will save yourself time by asking
instead on forums like StackOverflow that are geared to helping people
for such general or novice kinds questions and tasks. And unless you
are a sponsor of the project, if your question seems to be of this
category, the issue may just be closed.

Also, the unless you are a sponsor of the project, it may take a
while, maybe a week or so, before the bug report is noticed, let alone
acted upon.

To set expectations, some legitimate bugs can take years to fix, but
they eventually do get fixed.

Funding the project was added to partially address the problem that there are
lots of people seeking help and reporting bugs, but few people who are
willing or capable of providing help or fixing bugs.

Tasks or the kinds of things others can do, but you can't do or don't
want to do yourself are typically the kind of thing that you pay
someone to do, especially when you are the primary beneficiary of the
work, or the task is complex, long, or tedious. If your code is over
30 lines long, it fits into this category.


See also https://github.com/rocky/python-uncomp[yle6/blob/master/HOW-TO-REPORT-A-BUG.md ?
-->

<!--
Please remove any of the optional sections if they are not applicable.

Prerequisites/Caveats

* Make sure the bytecode you have can be disassembled with a
  disassembler and produces valid results.
* Try to make the bytecode that exhibits a bug as small as possible.
* Don't put bytecode and corresponding source code on any service that
  requires registration to download. Instead attach it as a zip file.
* When you open a bug report there is no privacy. If you need privacy, then
  contact me by email and explain who you are and the need for privacy.
  But be mindful that you may be asked to sponsor the project for the
  personal and private help that you are requesting.
* If the legitimacy of the activity is deemed suspicious, I may flag it as suspicious,
  making the issue even more easy to detect.

Bug reports that violate the above may be discarded.

-->

## Description

<!-- Please add a clear and concise description of the bug. Try to narrow the problem down to the smallest that exhibits the bug.-->

## How to Reproduce

<!-- Please show both the *input* you gave and the
output you got in describing how to reproduce the bug:

or give a complete console log with input and output

```console
$ uncompyle6 <command-line-options>
...
$
```

Attach a zip file to the Python bytecode or a
gist with the information. If you have the correct source code, you
can add that too.

-->

## Output Given

<!--
Please include not just the error message but all output leading to the message which includes echoing input and messages up to the error.
For a command-line environment include command invocation and all the output produced.

If this is too long, then try narrowing the problem to something short.
-->


## Expected behavior

<!-- Add a clear and concise description of what you expected to happen. -->

## Environment

<!-- _This section sometimes is optional but helpful to us._

Please modify for your setup

- Uncompyle6 version: output from  `uncompyle6 --version` or `pip show uncompyle6`
- xdis version: output from `pydisasm --version` or or `pip show xdis`
- Python version for the version of Python the byte-compiled the file: `python -c "import sys; print(sys.version)"` where `python` is the correct CPython or PyPy binary.
- OS and Version: [e.g. Ubuntu bionic]

-->

## Workarounds

<!-- If there is a workaround for the problem, describe that here. -->

## Priority

<!-- If this is important for a particular public good state that here.
     If this is blocking some important activity let us know what activity it blocks.

	 Otherwise, we'll assume this has the lowest priority in addressing.
	 -->

## Additional Context

<!-- _This section is optional._

Add any other context about the problem here or special environment setup.

-->
