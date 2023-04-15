# Bug was erroneously putting quotes around Exception on decompilatoin
# RUNNABLE!

"""This program is self-checking!"""
z = ["y", Exception]
assert z[0] == "y"
assert isinstance(z[1], Exception)
