import asyncio
import itertools
import pak

class CyclingByteStream:
    def __init__(self, data):
        self.data = iter(itertools.cycle(bytearray(data)))

    async def read(self, n=-1):
        if n < 0:
            raise ValueError("Cannot read all of infinite byte stream")

        await pak.util.yield_exec()

        # Take 'n' bytes from the infinitely cycling data.
        extracted_data = b"".join(x.to_bytes(1, "little") for _, x in zip(range(n), self.data))

        return extracted_data

    async def readexactly(self, n):
        return await self.read(n)
