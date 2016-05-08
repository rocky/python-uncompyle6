# Bug in &= ~x in Python 3
# Uses DUP_TOP_TWO in Python 3 and
# DUP_TOPX_2 in Python 2
import sys, termios
new = sys.argv[:]
new[3] &= ~termios.ECHO
