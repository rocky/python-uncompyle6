# Self-checking test.
# Tests:
#  for ::= SETUP_LOOP expr for_iter store
#          for_block POP_BLOCK COME_FROM
# In 3.8+
#  for ::= expr for_iter store
#          for_block POP_BLOCK COME_FROM

c = 0
for a in [1]:
    c += a
assert c == 1, c

for a in range(3):
    c += a

assert c == 4, c
