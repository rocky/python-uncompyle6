# From 3.6 base64.py
# Bug was handling "and" condition in the presense of POP_JUMP_IF_FALSE
# locations
def _85encode(foldnuls, words):
    return ['z' if foldnuls and word
                else  'y'
                for word in words]
