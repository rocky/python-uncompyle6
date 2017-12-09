# Bug in 3.5 cmd.py
# Bug is "while and" not getting handled properly
i, n = 0, 5
while i < n and __file__ in (1,2): i += 1
