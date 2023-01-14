# Related to #426

# This file is RUNNABLE!
"""This program is self-checking!"""

a = 5
class MakeClosureTest():
    # This function uses MAKE_CLOSURE with annotation args
    def __init__(self, dev: str, b: bool):
        super().__init__()
        self.dev = dev
        self.b = b
        self.a = a

x = MakeClosureTest("dev", True)
assert x.dev == "dev"
assert x.b == True
assert x.a == 5
