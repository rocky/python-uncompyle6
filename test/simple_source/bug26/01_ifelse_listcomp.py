# Bug from issue #171:  parsing "if x if a else y" inside a list comprehension on 2.7
# This is RUNNABLE!
assert [False, True, True, True, True] == [False if not a else True for a in range(5)]
assert [True, False, False, False, False] == [False if a else True for a in range(5)]
