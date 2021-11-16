import asyncio
import itertools
import pak

from dolor import *

def assert_type_marshal(type_cls, *values_and_data, ctx=None):
    for value, data in values_and_data:
        data_from_value = type_cls.pack(value, ctx=ctx)
        value_from_data = type_cls.unpack(data, ctx=ctx)

        assert data_from_value == data,  f"data_from_value={data_from_value}; data={data}; value={value}"
        assert value_from_data == value, f"value_from_data={value_from_data}; value={value}; data={data}"

def assert_type_marshal_func(*args, **kwargs):
    # Use this if you only need to compare values
    # and raw data and can compare the values using
    # equality.
    #
    # For anything else, you should create your own
    # function, potentially using assert_type_marshal.

    return lambda: assert_type_marshal(*args, **kwargs)

def assert_packet_marshal(*values_and_data, ctx=None):
    for value, data in values_and_data:
        # Remove the ID from the packet data.
        data_file = pak.util.file_object(data)
        Packet._id_type.unpack(data_file, ctx=ctx)

        data_from_value = value.pack(ctx=ctx)
        value_from_data = value.unpack(data_file, ctx=ctx)

        assert data_from_value == data,  f"data_from_value={data_from_value}; data={data}; value={value}"
        assert value_from_data == value, f"value_from_data={value_from_data}; value={value}; data={data}"

def assert_packet_marshal_func(*args, **kwargs):
    # Use this if you only need to compare values
    # and raw data and can compare the values using
    # equality.
    #
    # For anything else, you should create your own
    # function, potentially using assert_packet_marshal.

    return lambda: assert_packet_marshal(*args, **kwargs)

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
        self.data = itertools.cycle(bytearray(data))

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
