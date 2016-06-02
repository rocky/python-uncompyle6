# Bug from python2.6/SimpleXMLRPCServer.py
# The problem in 2.6 is handling

#  72 JUMP_ABSOLUTE           17 (to 17)
#  75 POP_TOP
#  76 JUMP_ABSOLUTE           17 (to 17)

# And getting:
# list_for ::= expr _for designator list_iter JUMP_BACK
# list_iter ::= list_if JUMP_BACK
#                       ^^^^^^^^^ added to 2.6 grammar
# list_iter ::= list_for


def list_public_methods(obj):
    return [member for member in dir(obj)
                if not member.startswith('_') and
                    hasattr(getattr(obj, member), '__call__')]
