import asyncio

class AsyncValueHolder:
    def __init__(self):
        self.event = asyncio.Event()

    async def get(self):
        await self.event.wait()

        return self.value

    def set(self, value):
        self.value = value

        self.event.set()
