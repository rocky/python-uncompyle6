# From 2.6.9 abc.py

# For 2.6:
# genexpr_func ::= setup_loop_lf FOR_ITER store comp_iter JUMP_BACK come_from_pop JUMP_BACK POP_BLOCK COME_FROM

# This has been a bug in other Pythons after 2.6 were set comprehension {} is used instead of set().
abstracts = set(name
             for name, value in namespace.items()
             if getattr(value, "__isabstractmethod__", False))
