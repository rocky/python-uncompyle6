# from 3.7 test_contextlib_async.py
# Bugs were not adding "async" when a function is a decorator,
# and a misaligment when using "async with ... as".

"""This program is self-checking!"""
import asyncio
from contextlib import asynccontextmanager, AbstractAsyncContextManager
import functools


def _async_test(func):
    """Decorator to turn an async function into a test case."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        coro = func(*args, **kwargs)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()
            asyncio.set_event_loop(None)

    return wrapper


state = []


@asynccontextmanager
async def woohoo():
    state.append(1)
    yield 42
    state.append(999)


@_async_test
async def test_enter():
    class DefaultEnter(AbstractAsyncContextManager):
        async def __aexit__(*args):
            return
            # await super().__aexit__(*args)

    manager = DefaultEnter()
    got_manager = await manager.__aenter__()
    # print(got_manager, manager)
    assert got_manager is manager

    async with manager as context:
        async with woohoo() as x:
            x = 1
            y = 2
        assert manager is context


# From 3.7.6 test_coroutines.py
# Bug was different form of code for "async with" below
class CoroutineTest:
    def test_with_8(self):
        CNT = 0

        async def foo():
            nonlocal CNT
            async with CM():
                CNT += 1
                return


test_enter()
