# Ensure PyPy handling of:
#    key, value in slotstate.items().
# PyPy uses LOOKUP_METHOD and CALL_METHOD instead
# of LOAD_ATTR and CALL_FUNCTION
def bug(state, slotstate):
    if state:
        if slotstate is not None:
            for key, value in slotstate.items():
                setattr(state, key, 2)
