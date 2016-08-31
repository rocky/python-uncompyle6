# From python 3.4 difflib
# Bug in 3.x is combining bestsize +=1 with while condition
bestsize = 5
b = [2]
def isbjunk(x):
    return False

while 1 < bestsize and \
      not isbjunk(b[0]) and \
      b[0]:
    bestsize += 1
