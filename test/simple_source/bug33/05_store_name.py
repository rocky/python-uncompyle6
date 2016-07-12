# From 3.3.5 turtledemo/bytedesign.py
# Python 3.2 and 3.3 adds this funny
# LOAD_FAST STORE_LOCALS
# which we translate to
# # inspect.currentframe().f_locals = __locals__
from turtle import Turtle
class Designer(Turtle):
    def design(self, homePos, scale):
        pass
