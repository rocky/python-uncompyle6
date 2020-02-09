async def a(b, c):
    async for b in c:
        pass

# From 3.7 test_generators.py
# Bug was getting indentation correct for multiple async's
async def foo(X):
    async for i in X:
        pass
    async for i in X:
        pass
    raise Done
