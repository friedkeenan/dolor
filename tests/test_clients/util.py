import inspect
import zlib
import pytest

from ..util import ByteStream

from dolor import *

__all__ = [
    "ClientTest",
    "client_test",
]

class ClientTest(Client):
    received_data    = None

    reader_cls = ByteStream
    writer_cls = ByteStream

    def __init__(self, address="test_address", *args, version=Version.latest(), **kwargs):
        super().__init__(address, *args, version=version, **kwargs)

        self.sent_packets = []

    async def write_packet_instance(self, packet):
        self.sent_packets.append(packet)

        return await super().write_packet_instance(packet)

    @property
    def sent_data(self):
        return self.writer.data

    def pack_packets(self, iterable):
        # Handle compression when a 'SetCompressionPacket' is encountered.
        compression_threshold = -1
        packed_packets = []
        for packet in iterable:
            packet_data = packet.pack(ctx=self.ctx)

            if compression_threshold >= 0:
                written_data_len = 0
                real_data_len    = len(packet_data)

                if real_data_len > compression_threshold:
                    data_len    = real_data_len
                    packet_data = zlib.compress(packet_data)

                packet_data = types.VarInt.pack(written_data_len, ctx=self.ctx) + packet_data

            packed_packets.append(packet_data)

            if isinstance(packet, clientbound.SetCompressionPacket):
                compression_threshold = packet.threshold

        return b"".join(
            types.VarInt.pack(len(packet_data), ctx=self.ctx) + packet_data

            for packet_data in packed_packets
        )

    def received_packets(self):
        return None

    async def startup(self):
        received_packets = self.received_packets()

        if self.received_data is None and received_packets is None:
            raise TypeError("One of 'received_data' and 'received_packets' must be set")

        if self.received_data is not None and received_packets is not None:
            raise TypeError("Only one of 'received_data' and 'received_packets' must be set")

        if self.received_data is not None:
            raw_packet_data = self.received_data
        else:
            raw_packet_data = self.pack_packets(received_packets)

        self.reader = self.reader_cls(raw_packet_data)
        self.writer = self.writer_cls()

def client_test(client_cls=None, caller_frame=None, **kwargs):
    if caller_frame is None:
        caller_frame = inspect.currentframe().f_back

    if client_cls is None:
        return lambda client_cls: client_test(client_cls, caller_frame, **kwargs)

    new_cls = type(client_cls.__name__, (client_cls, ClientTest), dict(
        __module__ = client_cls.__module__,
    ))

    @pytest.mark.asyncio
    async def test():
        await new_cls(**kwargs).start()

    # Set variable in the caller's scope
    caller_frame.f_globals[f"test_{client_cls.__name__}"] = test

    return new_cls
