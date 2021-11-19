import asyncio
import pytest

from dolor import *

def test_register():
    handler = PacketHandler()

    async def listener(packet):
        pass

    def bogus_listener(packet):
        pass

    with pytest.raises(TypeError, match="bogus_listener"):
        handler.register_packet_listener(bogus_listener, Packet)

    with pytest.raises(TypeError, match="packet checker"):
        handler.register_packet_listener(listener)

    handler.register_packet_listener(listener, Packet)

    with pytest.raises(ValueError, match="registered"):
        handler.register_packet_listener(listener, Packet)

    assert handler.is_listener_registered(listener)
    assert not handler.is_listener_registered(bogus_listener)

    handler.unregister_packet_listener(listener)
    assert not handler.is_listener_registered(listener)

def test_checkers():
    handler = PacketHandler()
    conn    = Connection(serverbound, version=Version.latest())

    async def listener(packet):
        pass

    handler.register_packet_listener(listener, ServerboundPacket)

    assert handler.listeners_for_packet(conn, ServerboundPacket()) == [listener]
    assert handler.listeners_for_packet(conn, ClientboundPacket()) == []

    handler.unregister_packet_listener(listener)
    assert handler.listeners_for_packet(conn, ServerboundPacket()) == []

    handler.register_packet_listener(listener, 0x00)

    assert handler.listeners_for_packet(conn, serverbound.HandshakePacket()) == [listener]
    assert handler.listeners_for_packet(conn, GenericPacketWithID(0x00))     == [listener]
    assert handler.listeners_for_packet(conn, GenericPacketWithID(0x01))     == []

    handler.unregister_packet_listener(listener)

    handler.register_packet_listener(listener, lambda packet: isinstance(packet, GenericPacket) and packet.data == b"test")

    assert handler.listeners_for_packet(conn, GenericPacket(data=b"test")) == [listener]
    assert handler.listeners_for_packet(conn, GenericPacket(data=b""))     == []
    assert handler.listeners_for_packet(conn, ServerboundPacket())         == []

    handler.unregister_packet_listener(listener)

    handler.register_packet_listener(listener, lambda conn, packet: packet.id(ctx=conn.ctx) < 0x02)

    assert handler.listeners_for_packet(conn, GenericPacketWithID(0x00)) == [listener]
    assert handler.listeners_for_packet(conn, GenericPacketWithID(0x01)) == [listener]
    assert handler.listeners_for_packet(conn, GenericPacketWithID(0x02)) == []

    handler.unregister_packet_listener(listener)

    handler.register_packet_listener(listener, ServerboundPacket, ClientboundPacket)

    assert handler.listeners_for_packet(conn, ServerboundPacket()) == [listener]
    assert handler.listeners_for_packet(conn, ClientboundPacket()) == [listener]
    assert handler.listeners_for_packet(conn, Packet())            == []

@pytest.mark.asyncio
async def test_listener_tasks():
    handler = PacketHandler()
    conn    = Connection(serverbound, version=Version.latest())

    async def unending_listener(packet):
        packet.did_execute_task = True

        while True:
            await asyncio.sleep(0)

    handler.register_packet_listener(unending_listener, Packet)
    async with handler.listener_task_context(listen_sequentially=False):
        packet = Packet()

        for listener in handler.listeners_for_packet(conn, packet):
            handler.create_listener_task(listener(packet))

    try:
        await asyncio.wait_for(handler.end_listener_tasks(timeout=0), 1)
    except asyncio.TimeoutError:
        # This should never happen since 'unending_listener' should get canceled.
        assert False

    assert packet.did_execute_task

    # TODO: Figure out how to test listening sequentially.
