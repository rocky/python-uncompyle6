# This is a seperate test pattern, since 'continue' within 'try'
# was not allowed till Python 2.1

for term in args:
    try:
        print
        continue
        print
    except:
        pass
