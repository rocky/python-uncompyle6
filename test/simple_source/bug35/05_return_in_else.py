# Bug in 3.5 _pydecimal.py was erroriously thinking the
# return after the "else" was an "end if"

def parseline(self, line):
    if not line:
        return 5
    elif line:
        if hasattr(self, 'do_shell'):
            line = 'shell'
        else:
            return 3 if line[3] else 4
    return 6

# From 3.5 gettext.py
# In the below code, the "return" was erroneously
# classifying RETURN_END_IF instead of RETURN_VALUE
def find(domain):
    for lang in domain:
        if lang:
            if all:
                domain.append(5)
            else:
                return lang
    return domain
