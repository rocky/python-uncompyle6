# Bug is turning a JUMP_BACK for a CONTINUE so for has no JUMP_BACK.
# Also there is no POP_BLOCK since there isn't anything in the loop.
# In the future when we have better control flow, we might redo all of this.
for i in range(2):
    pass
