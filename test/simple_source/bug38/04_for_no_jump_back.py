# from mult_by_const/instruction.py
# Bug in 3.8 was handling no JUMP_BACK in "for" loop. It is
# in the "if" instead

# RUNNABLE!
def instruction_sequence_value(instrs, a, b):
    for instr in instrs:
        if a:
            a = 6
        elif b:
            return 0
        pass

    return a

assert instruction_sequence_value([], True, True) == 1
assert instruction_sequence_value([1], True, True) == 6
assert instruction_sequence_value([1], False, True) == 0
assert instruction_sequence_value([1], False, False) == False
