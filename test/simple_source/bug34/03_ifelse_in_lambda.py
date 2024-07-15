# Next line is 1164
def foo():
    name = "bar"
    lambda x: compile(x, "<register %s's commit>" % name, "exec") if x else None
