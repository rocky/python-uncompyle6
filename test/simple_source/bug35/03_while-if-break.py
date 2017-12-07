# Python 3.5 and 3.6 break inside a
# while True and if / break
def display_date(loop):
    while True:
        if loop:
            break
        x = 5

    # Another loop to test 3.5 ifelsestmtl grammar rule
    while loop:
        if x:
            True
        else:
            True
