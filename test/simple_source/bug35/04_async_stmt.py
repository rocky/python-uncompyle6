# From 3.5 _collections.abc.py
# Bug was not having \n after "await self.athrow()" stmt
async def aclose(self):
    try:
        await self.athrow()
    except (GeneratorExit):
        pass
    else:
        raise RuntimeError
