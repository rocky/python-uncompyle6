if __file__ == ['-']:
    while True:
        try:
            compile(__file__, doraise=True)
        except RuntimeError:
            rv = 1
else:
    rv = 1
print(rv)


while 1:pass
