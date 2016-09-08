# Bug from Python 3.3 _markupbase.py cross compilatin
# error in unmarshaling a frozenset
import sys
if sys.argv[0] in frozenset({"attlist", "linktype", "link", "element"}):
    print("Yep")
