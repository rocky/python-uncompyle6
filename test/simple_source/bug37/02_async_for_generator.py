# From 3.7 test_asyncgen.py
# Bug is handling new "async for" lingo
def make_arange(n):
    # This syntax is legal starting with Python 3.7
    return (i * 2 async for i in n)

async def run(m):
    return [i async for i in m]

# From 3.7.6 test_coroutines.py
async def run_list(pair, f):
    return [i for pair in p async for i in f]

# FIXME: add this. It works in decompyle3
# async def run_gen():
#     return (i async for i in f if 0 < i < 4)
