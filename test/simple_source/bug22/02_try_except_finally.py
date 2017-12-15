# Adapted from Python 2.4 bdb.py runeval()

# In Python 2.4 and before, try/finally has to be one block
# and try/except has to be in a separate block.

# In Python 2.5 and later, these can be combined into one "try" block,
# and indeed compiling this in 2.5+ will in fact combine the blocks.
# And that's okay, even if it might not be what was written.

# However for 2.4 and before make sure this _isn't_ combined into one block.
try:
    try:
        quitting = eval("1+2")
    except RuntimeError:
        pass
finally:
    quitting = 1
