# From 3.7.3 asyncio/base_events.py
# We had (still have) screwy logic. Python 3.5 code node detection was off too.

async def create_connection(self):
    infos = await self._ensure_resolved()

    laddr_infos = await self._ensure_resolved()
    for family in infos:
        for laddr in laddr_infos:
            family = 1
        else:
            continue
        await self.sock_connect()
    else:
        raise OSError('Multiple exceptions: {}' for exc in family)

    return
