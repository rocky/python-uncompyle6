from uncompyle6.semantics.fragments import code_deparse as deparse
from xdis.version_info import PYTHON_VERSION_TRIPLE

def map_stmts(x, y):
    x = []
    y = {}
    return x, y

def return_stmt(x, y):
        return x, y

def try_stmt():
    try:
        x = 1
    except:
        pass
    return x

def for_range_stmt():
    for i in range(2):
        i+1

# # FIXME: add this test - but for Python 2.7+ only
# def set_comp():
#     {y for y in range(3)}

# FIXME: add this test
def list_comp():
    [y for y in range(3)]

def get_parsed_for_fn(fn):
    code = fn.__code__
    return deparse(code, version=PYTHON_VERSION_TRIPLE)

def check_expect(expect, parsed, fn_name):
    debug = False
    i = 2
    max_expect = len(expect)
    for name, offset in sorted(parsed.offsets.keys()):
        assert i+1 <= max_expect, (
            "%s: ran out if items in testing node" % fn_name)
        nodeInfo = parsed.offsets[name, offset]
        node = nodeInfo.node
        extractInfo = parsed.extract_node_info(node)

        assert expect[i] == extractInfo.selectedLine, \
          ('%s: line %s expect:\n%s\ngot:\n%s' %
               (fn_name, i, expect[i], extractInfo.selectedLine))
        assert expect[i+1] ==  extractInfo.markerLine, \
                     ('line %s expect:\n%s\ngot:\n%s' %
                     (i+1, expect[i+1], extractInfo.markerLine))
        i += 3
        if debug:
            print(node.offset)
            print(extractInfo.selectedLine)
            print(extractInfo.markerLine)

        extractInfo, p = parsed.extract_parent_info(node)
        if extractInfo:
            assert i+1 < max_expect, "ran out of items in testing parent"
            if debug:
                print("Contained in...")
                print(extractInfo.selectedLine)
                print(extractInfo.markerLine)
            assert expect[i] == extractInfo.selectedLine, \
              ("parent line %s expect:\n%s\ngot:\n%s" %
               (i, expect[i], extractInfo.selectedLine))
            assert expect[i+1] == extractInfo.markerLine, \
              ("parent line %s expect:\n%s\ngot:\n%s" %
               (i+1, expect[i+1], extractInfo.markerLine))
            i += 3
        pass
    pass


def test_stuff():
    return
    parsed = get_parsed_for_fn(map_stmts)
    expect = """
-1
return (x, y)
             ^
Contained in...
return (x, y)
-------------
0
x = []
    -
Contained in...
x = []
    --
3
x = []
-
Contained in...
x = []
------
6
y = {}
    -
Contained in...
y = {}
    --
9
y = {}
-
Contained in...
y = {}
------
12
return (x, y)
        -
Contained in...
return (x, y)
       ------
15
return (x, y)
           -
Contained in...
return (x, y)
       ------
18
return (x, y)
       ------
Contained in...
return (x, y)
-------------
21
return (x, y)
-------------
Contained in...
x = [] ...
------ ...
""".split("\n")
    check_expect(expect, parsed, 'map_stmts')
    ########################################################
    # return

    parsed = get_parsed_for_fn(return_stmt)
    expect = """
-1
return (x, y)
             ^
Contained in...
return (x, y)
-------------
0
return (x, y)
        -
Contained in...
return (x, y)
       ------
3
return (x, y)
           -
Contained in...
return (x, y)
       ------
6
return (x, y)
       ------
Contained in...
return (x, y)
-------------
9
return (x, y)
-------------
Contained in...
return (x, y)
-------------
""".split("\n")
    check_expect(expect, parsed, 'return_stmt')
    ########################################################
#     # try

#     expect = """
# -1
# return (x, y)
#              ^
# Contained in...
# return (x, y)
# -------------
# 0
# try:
# ----
# Contained in...
# try: ...
# ---- ...
# 3
#     x = 1
#         -
# Contained in...
#     x = 1
#     -----
# 6
#     x = 1
#     -
# Contained in...
#     x = 1
#     -----
# 9
#     pass
#         ^
# Contained in...
# try: ...
# ---- ...
# 10
# except:
#         ^
# Contained in...
# except: ...
# ------- ...
# 19
#     pass
#         ^
# Contained in...
# except: ...
# ------- ...
# 13_0
# except:
#         ^
# Contained in...
# except: ...
# ------- ...
# 20_0
#     pass
#         ^
# Contained in...
# except: ...
# ------- ...
# """.split("\n")
#     parsed = get_parsed_for_fn(try_stmt)
#     check_expect(expect, parsed)

#     ########################################################
#     # for range
    expect = """
0
for i in range(2):
    -
Contained in...
for i in range(2): ...
------------------ ...
3
for i in range(2):
         -----
Contained in...
for i in range(2):
         --------
6
for i in range(2):
               -
Contained in...
for i in range(2):
         --------
9
for i in range(2):
         --------
Contained in...
for i in range(2): ...
------------------ ...
12
for i in range(2):
    -
Contained in...
for i in range(2): ...
------------------ ...
13
for i in range(2):
    -
Contained in...
for i in range(2): ...
------------------ ...
16
for i in range(2):
    -
Contained in...
for i in range(2): ...
------------------ ...
19
    i + 1
    -
Contained in...
    i + 1
    -----
22
    i + 1
        -
Contained in...
    i + 1
    -----
25
    i + 1
      -
Contained in...
    i + 1
    -----
27
return
      ^
Contained in...
    i + 1
    -----
31
return
------
Contained in...
for i in range(2): ...
------------------ ...
34
return
------
Contained in...
for i in range(2): ...
------------------ ...
.
""".split("\n")
    parsed = get_parsed_for_fn(for_range_stmt)
