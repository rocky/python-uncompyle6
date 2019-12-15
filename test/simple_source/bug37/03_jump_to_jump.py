# From uncompyle6/verify.py
# Bug was POP_JUMP offset to short so we have a POP_JUMP
# to a JUMP_ABSOULTE and this messes up reduction rule checking.

def cmp_code_objects(member, a, tokens1, tokens2, verify, f):
    for member in members:
        while a:
            # Increase the bytecode length of the while statement
            x = 1; x = 2; x = 3; x = 4; x = 5; x = 6; x = 7; x = 8
            x = 1; x = 2; x = 3; x = 4; x = 5; x = 6; x = 7; x = 8
            x = 1; x = 2; x = 3; x = 4; x = 5; x = 6; x = 7; x = 8
            x = 1; x = 2; x = 3; x = 4; x = 5; x = 6; x = 7; x = 8
            x = 1; x = 2; x = 3; x = 4; x = 5; x = 6; x = 7; x = 8
            x = 1; x = 2; x = 3; x = 4; x = 5; x = 6; x = 7; x = 8
            x = 49; x = 50; x = 51; x = 52; x = 53;
            if tokens1:
                if tokens2:
                    continue
                elif f:
                    continue
            else:
                a = 2

            i1 += 1
            x = 54 # comment this out and we're good
