"""Here we have "scanners" for the different Python versions.
"scanner" is a compiler-centric term, but it is really a bit different from
a traditional  compiler scanner/lexer.

Here we start out with text disasembly and change that to be more
ameanable to parsing in which we look only at the opcode name, and not
and instruction's operand.

In some cases this is done by changing the opcode name. For example
"LOAD_CONST" it customized based on the type of its operand into
"LOAD_ASSERT", "LOAD_CODE", "LOAD_STR".

instructions that take a variable number of arguments will have the argument count
suffixed to the opcode name. "CALL", "MAKE_FUNCTION", "BUILD_TUPLE", "BUILD_LIST",
work this way for example

We also add pseudo instructions like "COME_FROM" which have an operand

Instead of full grammars, we have full grammars for certain Python versions
and the others indicate differences between a neighboring version.

For example Python 2.6, 2.7, 3.2, and 3.7 are largely "base" versions
which work off of scanner2.py, scanner3.py, and scanner37base.py.

Some examples:
Python 3.3 diffs off of 3.2; 3.1 and 3.0 diff off of 3.2; Python 1.0..Python 2.5 diff off of
Python 2.6 and Python 3.8 diff off of 3.7

"""
