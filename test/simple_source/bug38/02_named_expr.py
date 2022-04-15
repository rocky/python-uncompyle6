# From 3.8 test_named_expressions.py
# Bug was not putting parenthesis around := below
# RUNNABLE!

"""This program is self-checking!"""
(a := 10)
assert a == 10

# Bug was not putting all of the levels of parentheses := below

(z := (y := (x := 0)))
assert x == 0
assert y == 0
assert z == 0
