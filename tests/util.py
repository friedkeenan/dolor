import asyncio
import itertools

class ByteStream:
    def __init__(self, data=b""):
        if not isinstance(data, bytearray):
            data = bytearray(data)

        self.data        = data
        self.close_event = asyncio.Event()

    async def read(self, n=-1):
        # Yield.
        await asyncio.sleep(0)

        if n < 0:
            n = len(self.data)

        extracted_data = self.data[:n]
        self.data      = self.data[n:]

        return extracted_data

    async def readexactly(self, n):
        # Yield.
        await asyncio.sleep(0)

        if n > len(self.data):
            raise asyncio.IncompleteReadError(expected=n, partial=self.data[:n])

        return await self.read(n)

    def write(self, new_data):
        self.data.extend(new_data)

    async def drain(self):
        # Yield.
        await asyncio.sleep(0)

    def close(self):
        self.close_event.set()

    def is_closing(self):
        return self.close_event.is_set()

    async def wait_closed(self):
        await self.close_event.wait()

class CyclingByteStream:
    def __init__(self, data):
        self.data = iter(itertools.cycle(bytearray(data)))

    async def read(self, n=-1):
        if n < 0:
            raise ValueError("Cannot read all of infinite byte stream")

        # Yield.
        await asyncio.sleep(0)

        # Take 'n' bytes from the infinitely cycling data.
        extracted_data = b"".join(x.to_bytes(1, "little") for _, x in zip(range(n), self.data))

        return extracted_data

    async def readexactly(self, n):
        return await self.read(n)
