# Python 3.5+ async and await
async def await_test(asyncio):
    reader, writer = await asyncio.open_connection(80)
    await bar()

async def afor_test():

    async for i in [1,2,3]:
        x = i


async def afor_else_test():

    async for i in [1,2,3]:
        x = i
    else:
        z = 4


async def awith_test():
    async with i:
        print(i)

async def awith_as_test():
    async with 1 as i:
        print(i)

async def f(z):
    await z

async def g(z):
    return await z
