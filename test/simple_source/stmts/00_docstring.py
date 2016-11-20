# uncompyle2 bug was not escaping """ properly
r'''func placeholder - with ("""\nstring\n""")'''
def foo():
    r'''func placeholder - ' and with ("""\nstring\n""")'''

def bar():
    r"""func placeholder - ' and with ('''\nstring\n''') and \"\"\"\nstring\n\"\"\" """
