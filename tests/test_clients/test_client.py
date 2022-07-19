import asyncio
import pak
import pytest

from dolor import *

from .util import client_test, ClientTest

from ..util import CyclingByteStream

@client_test
class GenericPacketTest(Client):
    received_data = (
        # There is no packet with ID 0x69 in the handshaking state.
        (b"\x05" + b"\x69" + b"test") * 2
    )

    async def on_start(self):
        packet = None

        async for received_packet in self.continuously_read_packets():
            if packet is None:
                packet = received_packet

                assert packet.id(ctx=self.ctx) == 0x69
                assert packet.data == b"test"
            else:
                assert received_packet.id(ctx=self.ctx) == 0x69

                assert received_packet ==     packet
                assert received_packet is not packet

                # Make sure they have the exact same type (due to caching).
                assert type(received_packet) is type(packet)

@client_test
class SpecificReadTest(Client):
    received_data = (
        b"\x05" + b"\x69" + b"test"
    )

    reader_cls = CyclingByteStream

    async def on_start(self):
        async def continuous_read_task():
            async for _ in self.continuously_read_packets():
                pass

        continuous_task = asyncio.create_task(continuous_read_task())

        packet = await self.read_packet(GenericPacketWithID(0x69))
        assert packet.data == b"test"

        continuous_task.cancel()

@client_test
class ClosedSpecificReadTest(Client):
    received_data = b""

    async def on_start(self):
        async def specific_read_task():
            return await self.read_packet(GenericPacketWithID(0x69))

        specific_task = asyncio.create_task(specific_read_task())

        async for _ in self.continuously_read_packets():
            # This code should never execute since we have no incoming data.
            assert False

        assert await specific_task is None

@client_test
class WritePacketTest(Client):
    received_data = b""

    async def on_start(self):
        await self.write_packet(GenericPacketWithID(0x69), data=b"test")

        assert self.sent_data == (
            b"\x05" + b"\x69" + b"test"
        )

        assert self.listener_called

    @pak.packet_listener(GenericPacketWithID(0x69), outgoing=True)
    async def outgoing_listener(self, packet):
        assert packet.data == b"test"

        self.listener_called = True

@client_test
class IncomingPacketListenTest(Client):
    received_data = (
        b"\x05" + b"\x69" + b"test"
    )

    async def on_start(self):
        await self._listen_to_incoming_packets()

        assert self.listener_called

    @pak.packet_listener(GenericPacketWithID(0x69))
    async def incoming_listener(self, packet):
        assert packet.data == b"test"

        self.listener_called = True

@client_test(version="1.12.2")
class StatustTest(Client):
    def received_packets(self):
        return [
            self.create_packet(
                clientbound.PongPacket,

                # Can't get the payload correct here since it requires the current time.
                payload = 0,
            ),

            self.create_packet(
                clientbound.ResponsePacket,

                response = clientbound.ResponsePacket.Response.Response(
                    version = Version("1.12.2"),

                    players = clientbound.ResponsePacket.Response.PlayersInfo(
                        max    = 20,
                        online = 0,
                    ),

                    description = types.Chat.Chat("test description"),
                )
            ),
        ]

    async def on_start(self):
        response, _ = await self.status()

        assert response.version               == "1.12.2"
        assert response.players.max           == 20
        assert response.players.online        == 0
        assert response.description.flatten() == "test description"

        assert self.sent_packets[:2] == [
            self.create_packet(
                serverbound.HandshakePacket,

                protocol       = 340,
                server_address = "test_address",
                server_port    = 25565,
                next_state     = ConnectionState.Status,
            ),

            self.create_packet(serverbound.RequestPacket),

            # Cannot test ping packet since it requires the current time.
        ]

@client_test
class FailedStatusTest(Client):
    received_data = b""

    async def on_start(self):
        with pytest.raises(RuntimeError, match="status"):
            await self.status()

@client_test(version="1.12.2", name="username")
class OfflineLoginTest(Client):
    # Test against raw data to ensure compression works fine.

    received_data = (
        # Set compress packet with threshold 256.
        b"\x03" + b"\x03" + b"\x80\x02" +

        # Compressed login success packet with default UUID and username "diffname".
        b"\x30" + b"\x00" + b"\x02" + b"\x2400000000-0000-0000-0000-000000000000" + b"\x08diffname" +

        # Compressed large generic packet.
        b"\x0E" + b"\x82\x02" + b"\x78\x9C\xCB\xFC\x3F\xD2\x01\x00\x71\xe2\x00\x78"
    )

    async def on_start(self):
        await self.login()

        assert self.listener_called

        # Test that we updated our name.
        assert self.name == "diffname"

        # Test that packet compression works.
        assert self.sent_data == (
            # Handshake packet.
            b"\x13" + b"\x00" + b"\xD4\x02" + b"\x0Ctest_address" + b"\x63\xDD" + b"\x02" +

            # Login start packet.
            b"\x0A" + b"\x00" + b"\x08username" +

            # Compressed small generic packet.
            b"\x07" + b"\x00" + b"\x69" + b"small" +

            # Compressed large generic packet.
            b"\x0E" + b"\x82\x02" + b"\x78\x9C\xCB\xFC\x3F\xD2\x01\x00\x71\xe2\x00\x78"
        )

    @pak.packet_listener(GenericPacketWithID(0x69))
    async def listener(self, packet):
        assert packet == GenericPacketWithID(0x69)(data=b"\xFF" * (256 + 1))

        await self.write_packet(
            GenericPacketWithID(0x69),

            data = b"small",
        )

        await self.write_packet(
            GenericPacketWithID(0x69),

            # Compression threshold is 256.
            data = b"\xFF" * (256 + 1)
        )

        self.listener_called = True

@client_test(version="1.12.2", name="username")
class KeepAliveTest(Client):
    def received_packets(self):
        return [
            self.create_packet(
                clientbound.LoginSuccessPacket,

                # Default UUID.
                username = "username",
            ),

            self.create_packet(
                clientbound.KeepAlivePacket,

                keep_alive_id = 0x69,
            ),
        ]

    async def on_start(self):
        await self.login()

        assert self.sent_packets == [
            self.create_packet(
                serverbound.HandshakePacket,

                protocol       = 340,
                server_address = "test_address",
                server_port    = 25565,
                next_state     = ConnectionState.Login,
            ),

            self.create_packet(
                serverbound.LoginStartPacket,

                name = "username",
            ),

            self.create_packet(
                clientbound.KeepAlivePacket,

                keep_alive_id = 0x69,
            ),
        ]

class MultipleRunTest(ClientTest):
    run_count = 0

    def received_packets(self):
        return [
            self.create_packet(
                clientbound.LoginSuccessPacket,

                username = "username",
            ),
        ]

    async def on_start(self):
        type(self).run_count += 1

        await super().on_start()

        assert self.state == ConnectionState.Play

def test_multiple_run():
    client = MultipleRunTest(name="username")

    assert MultipleRunTest.run_count == 0

    client.run()
    assert MultipleRunTest.run_count == 1

    client.run()
    assert MultipleRunTest.run_count == 2
