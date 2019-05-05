# From 3.7.3 base64.py
# Bug was handling "and not" in an
# if/else in the presence of better Python bytecode generatation

# RUNNABLE!
def foo(foldnuls, word):
    x = 5 if foldnuls and not word else 6
    return x

for expect, foldnuls, word in (
        (6, True, True),
        (5, True, False),
        (6, False, True),
        (6, False, False)
        ):
   assert foo(foldnuls, word) == expect
