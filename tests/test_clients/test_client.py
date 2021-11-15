import pytest

from dolor import *

from .util import client_test

@client_test
class StatustTest(Client):
    received_data = (
        # Pong packet (can't get the payload correct here since it requires the current time).
        b"\x09" + b"\x01" + b"\x00" * 8 +

        # Response packet.
        b"\x78" + b"\x00" + b'\x76{"version":{"name":"1.12.2","protocol":340},"players":{"max":20,"online":0},"description":{"text":"test description"}}'
    )

    async def on_start(self):
        response, _ = await self.status()

        assert response.version               == "1.12.2"
        assert response.players.max           == 20
        assert response.players.online        == 0
        assert response.description.flatten() == "test description"

        assert self.sent_data.startswith(
            # Handshake packet.
            b"\x0B" + b"\x00" + b"\xD4\x02" + b"\x04test" + b"\x63\xDD" + b"\x01" +

            # Request packet.
            b"\x01" + b"\x00"

            # Cannot test ping packet since it requires the current time.
        )

@client_test
class FailedStatusTest(Client):
    received_data = b""

    async def on_start(self):
        with pytest.raises(RuntimeError, match="status"):
            await self.status()

@client_test
class GenericPacketTest(Client):
    received_data = (
        # There is no packet with ID 0x69 in the handshaking state.
        (b"\x04" + b"\x69" + b"\xAA\xBB\xCC") * 2
    )

    async def on_start(self):
        packet = None

        async for received_packet in self.continuously_read_packets():
            if packet is None:
                packet = received_packet

                assert packet.id(ctx=self.ctx) == 0x69
                assert packet.data == b"\xAA\xBB\xCC"
            else:
                assert received_packet.id(ctx=self.ctx) == 0x69

                assert received_packet ==     packet
                assert received_packet is not packet

                # Make sure they have the exact same type (due to caching).
                assert type(received_packet) is type(packet)
