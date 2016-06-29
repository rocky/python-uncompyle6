# Python 2.6.9 Cookie.py
# Problem in 2.6 is making sure
# the two JUMP_ABSOLUTES get turned into:
#          26  CONTINUE              7  '7'
#          29  JUMP_BACK             7  '7'
# The fact that the "continue" is on the same
# line as the "if" is important.

for K in items:
    if V: continue

#          32  CONTINUE              7  '7'
#          35 JUMP_FORWARD           1 (to 39)
for K,V in items:
    if V == "": continue
    if K not in attrs: continue
