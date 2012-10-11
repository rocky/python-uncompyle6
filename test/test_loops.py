for i in range(10):
    if i == 3:
        continue
    if i == 5:
        break
    print i,
else:
    print 'Else'
print

for i in range(10):
    if i == 3:
        continue
    print i,
else:
    print 'Else'

i = 0
while i < 10:
    i = i+1
    if i == 3:
        continue
    if i == 5:
        break
    print i,
else:
    print 'Else'
print

i = 0
while i < 10:
    i = i+1
    if i == 3:
        continue
    print i,
else:
    print 'Else'
    
for x, y in [(1,2),(3,4)]:
    if x in ['==', '>=', '>']:
        if '0' in y:
            print

for x in (1, 2, 3):
    if x == 1:
        print x

i = 0
while i < 10:
    i+=1
    for x in (1,2,3):
        for y in (1,2,3):
            if x == y and x == 1:
                while i < 10:
                    print x
                    break


