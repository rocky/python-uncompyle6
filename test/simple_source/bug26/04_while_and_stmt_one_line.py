# From Python 2.6/MimeWriter.py
#
# Bug is detecting that "del" starts a statement
# and is not: del not lines[-1] and lines[-1]
#
# A complicating factor is that the "while"
# and statement are on the same line.
lines = __file__.split("\n")
while lines and not lines[-1]: del lines[-1]
