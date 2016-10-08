# listComprehensions.py -- source test pattern for list comprehensions
#
# This simple program is part of the decompyle test suite.
#
# decompyle is a Python byte-code decompiler
# See http://www.goebel-consult.de/decompyle/ for further information

print [i*j for i in range(4)
       if i == 2
       for j in range(7)
       if (i+i % 2) == 0 ]
