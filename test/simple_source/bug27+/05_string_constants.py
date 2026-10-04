# See https://github.com/rocky/python-uncompyle6/issues/528
# RUNNABLE!

"""This program is self-checking!"""

x = 1
L = [239, 168, 254, 54, 235, 128, "fred"]
D = {239: 240, 168:169, 54:55, 128:129, "fred":"wilma"}
S = {239, 168, 254, 54, 235, 128, "fred"}

assert L[6] == "fred"
assert "fred" in S
assert D["fred"] == "wilma"
