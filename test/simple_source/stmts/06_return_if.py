# from 2.6.9 Bastion.py
# Should see in 2.6.9:
# return_if_stmt ::= ret_expr RETURN_END_IF come_from_pop

def Bastion(object, filter = lambda name: name[:1] != '_'):
    def get1(name, attribute, MethodType, object=object, filter=filter):
        if filter(name):
            attribute = getattr(object, name)
            if type(attribute) == MethodType:
                return attribute
        raise AttributeError, name
