# from 3.7 test_contextlib_async.py
# Bugs were not adding "async" when a function is a decorator,
# and a misaligment when using "async with as".
@_async_test
async def test_enter(self):
    self.assertIs(await manager.__aenter__(), manager)

    async with manager as context:
        async with woohoo() as x:
            x = 1
            y = 2
        assert manager is context
