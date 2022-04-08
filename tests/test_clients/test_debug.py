import pak
import pytest

from dolor import *

from .util import ClientTest

class LoggingTest(clients.LoggingClient, ClientTest):
    def received_packets(self):
        return [
            self.create_packet(
                clientbound.LoginSuccessPacket,

                # Default UUID.
                username = "username",
            ),

            self.create_packet(
                GenericPacketWithID(0x69),

                data = b"incoming",
            ),

            self.create_packet(
                clientbound.KeepAlivePacket,

                keep_alive_id = 1,
            ),
        ]

    @pak.packet_listener(GenericPacketWithID(0x69))
    async def send_outgoing_generic_packet(self, packet):
        await self.write_packet(
            GenericPacketWithID(0x69),

            data = b"outgoing",
        )

class OutgoingLoggingTest(LoggingTest):
    log_outgoing_packets = True

class GenericLoggingTest(LoggingTest):
    log_generic_packets = True

class OutgoingGenericLoggingTest(LoggingTest):
    log_outgoing_packets = True
    log_generic_packets  = True

def test_logging(capsys):
    client = LoggingTest(name="username")
    client.run()

    out, err = capsys.readouterr()

    assert err == ""

    assert out == (
        "Incoming: LoginSuccessPacket(uuid=UUID('00000000-0000-0000-0000-000000000000'), username='username')\n"
        "Incoming: KeepAlivePacket(keep_alive_id=1)\n"
    )

def test_outgoing_logging(capsys):
    client = OutgoingLoggingTest(version="1.12.2", name="username")
    client.run()

    out, err = capsys.readouterr()

    assert err == ""

    assert out == (
        "Outgoing: HandshakePacket(protocol=340, server_address='test_address', server_port=25565, next_state=<ConnectionState.Login: 2>)\n"
        "Outgoing: LoginStartPacket(name='username')\n"
        "Incoming: LoginSuccessPacket(uuid=UUID('00000000-0000-0000-0000-000000000000'), username='username')\n"
        "Incoming: KeepAlivePacket(keep_alive_id=1)\n"
        "Outgoing: KeepAlivePacket(keep_alive_id=1)\n"
    )

def test_generic_logging(capsys):
    client = GenericLoggingTest(name="username")
    client.run()

    out, err = capsys.readouterr()

    assert err == ""

    assert out == (
        "Incoming: LoginSuccessPacket(uuid=UUID('00000000-0000-0000-0000-000000000000'), username='username')\n"
        "Incoming: GenericPacketWithID(0x69)(data=bytearray(b'incoming'))\n"
        "Incoming: KeepAlivePacket(keep_alive_id=1)\n"
    )

def test_outgoing_generic_logging(capsys):
    client = OutgoingGenericLoggingTest(version="1.12.2", name="username")
    client.run()

    out, err = capsys.readouterr()

    assert err == ""

    assert out == (
        "Outgoing: HandshakePacket(protocol=340, server_address='test_address', server_port=25565, next_state=<ConnectionState.Login: 2>)\n"
        "Outgoing: LoginStartPacket(name='username')\n"
        "Incoming: LoginSuccessPacket(uuid=UUID('00000000-0000-0000-0000-000000000000'), username='username')\n"
        "Incoming: GenericPacketWithID(0x69)(data=bytearray(b'incoming'))\n"
        "Outgoing: GenericPacketWithID(0x69)(data=bytearray(b'outgoing'))\n"
        "Incoming: KeepAlivePacket(keep_alive_id=1)\n"
        "Outgoing: KeepAlivePacket(keep_alive_id=1)\n"
    )
