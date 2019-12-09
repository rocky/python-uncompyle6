(x, y) = "foo", 0
if x := __name__:
    y = 1
assert x == "__main__", "Walrus operator changes value"
assert y == 1, "Walrus operator branch taken"
