# 2.5.6 decimal.py
# Bug on 2.5 and 2.6 by incorrectly changing opcode to
# RETURN_VALUE to psuedo op: RETURN_END_IF
def _formatparam(param, value=None, quote=True):
    if value is not None and len(value) > 0:
        if isinstance(value, tuple):
            value = 'a'
        if quote or param:
            pass
        else:
            return '%s=%s' % (param, value)
    else:
        return param

# python 2.7 SimpleXMLRPCServer.py
# Bug was turning return into "pass"
def system_methodSignature(seflf, method_name):
    return 'signatures not supported'
