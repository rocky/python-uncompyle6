# In Python 3.2 JUMP_ABSOLUTE's (which can
# turn into COME_FROM's) are not optimized as
# they are in later Python's.
#
# So an if statement can jump to the end of a for loop
# which in turn jump's back to the beginning of that loop.
#
# Should handle in Python 3.2
#
#          98	JUMP_BACK         '16' statement after: names.append(name) to loop head
#       101_0	COME_FROM         '50' statement: if name == ...to fictional "end if"
#         101	JUMP_BACK         '16' jump as before to loop head

def _slotnames(cls):
    names = []
    for c in cls.__mro__:
        if "__slots__" in c.__dict__:
            slots = c.__dict__['__slots__']
            for name in slots:
                if name == "__dict__":
                    continue
                else:
                    names.append(name) # 3.2 bug here jumping to outer for
