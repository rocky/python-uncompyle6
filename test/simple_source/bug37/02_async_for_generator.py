# From 3.7 test_asyncgen.py
# Bug is handling new "async for" lingo
def make_arange(n):
    # This syntax is legal starting with Python 3.7
    return (i * 2 async for i in n)

async def run(m):
    return [i async for i in m]
