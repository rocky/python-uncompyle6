# From python2.6/_abcoll.py
# Bug was wrong code for "comp_for" giving
# "for  in x" instead of: "for x in y"
chain = (e for s in (self, other) for x in y)
