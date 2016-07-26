# From PyPy argparse, dedent.

# PyPY adds opcode JUMP_IF_NOT_DEBUG.
# This is the two argument form.
assert __name__ != '__main"', 'Indent decreased below 0.'

# From PyPy simple_interact.py
# PyPy uses POP_JUMP_IF_FALSE as well as POP_JUMP_IF_TRUE
# CPython only uses POP_JUMP_IF_TRUE
while 1:
    try:
        more = 10
    except EOFError:
        break
    more = len(__file__)
    assert not more, "FOO"
    assert not more
