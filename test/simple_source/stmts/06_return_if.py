# from 2.6.9 Bastion.py
# Should see in 2.6.9:
# return_if_stmt ::= return_expr RETURN_END_IF come_from_pop

def Bastion(object, filter = lambda name: name[:1] != '_'):
    def get1(name, attribute, MethodType, object=object, filter=filter):
        if filter(name):
            attribute = getattr(object, name)
            if type(attribute) == MethodType:
                return attribute
        raise AttributeError, name

# Also from 2.6
# The use of the "and" causes to COME_FROMs in the else clause
# ifelsestmt  ::= testexpr c_stmts_opt jf_cf_pop else_suite COME_FROM
def loop(select, use_poll=False):
    if use_poll and hasattr(select, 'poll'):
        poll_fun = 'b'
    else:
        poll_fun = 'a'
