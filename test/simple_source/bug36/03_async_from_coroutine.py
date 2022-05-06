# These are from 3.6 test_coroutines.py
async def iterate(gen):
    res = []
    async for i in gen:
        res.append(i)
    return res

def test_comp_5(f):
    # async def f(it):
    #     for i in it:
    #         yield i

    async def run_list():
        return [i
                for
                pair in
                ([10, 20])
                async for i
                in f
                ]

async def test2(x, buffer, f):
    with x:
        async for i in f:
            if i:
                break
        else:
            buffer()
    buffer()

async def test3(x, buffer, f):
    with x:
        async for i in f:
            if i:
                continue
            buffer()
        else:
            buffer.append()
    buffer()
