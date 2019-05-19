# Tests all the different kinds of imports
import sys
from os import path
from os import *
import time as time1, os as os1
import http.client as httpclient
if len(__file__) == 0:
    # a.b.c should force consecutive LOAD_ATTRs
    import a.b.c as d
    import stuff0.stuff1.stuff2.stuff3 as stuff3
