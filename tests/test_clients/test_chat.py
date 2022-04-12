import pak
import pytest

from dolor import *

from .util import ClientTest

class ChatTest(clients.ChatClient, ClientTest):
    def received_packets(self):
        return [
            self.create_packet(
                clientbound.LoginSuccessPacket,

                # Default UUID.
                username = "username",
            ),

            self.create_packet(clientbound.JoinGamePacket),

            self.create_packet(
                clientbound.ChatMessagePacket,

                message  = "game info",
                position = enums.ChatPosition.GameInfo,
            ),

            self.create_packet(
                clientbound.ChatMessagePacket,

                message = "chat",
                position = enums.ChatPosition.Chat,
            ),
        ]

    def __init__(self, *args, value_holder, **kwargs):
        super().__init__(*args, **kwargs)

        self.value_holder = value_holder

    @pak.packet_listener(clientbound.ChatMessagePacket)
    async def send_input_to_chat(self, packet):
        if packet.position != enums.ChatPosition.GameInfo:
            return

        self.value_holder.set("input")

class ChatInputTest(ChatTest):
    send_input = True

# Must be async so that we can construct our value holder.
@pytest.mark.asyncio
async def test_chat_client(capsys, monkeypatch):
    value_holder = util.AsyncValueHolder()

    async def mock_ainput(*args, **kwargs):
        return await value_holder.get()

    monkeypatch.setattr("dolor.clients.chat.ainput", mock_ainput)

    client = ChatTest(value_holder=value_holder, name="username")
    await client.start()

    out, err = capsys.readouterr()

    assert err == ""

    assert out == (
        "GameInfo: game info\n"
        "Chat: chat\n"
    )

    assert client.create_packet(serverbound.ChatMessagePacket, message="input") not in client.sent_packets

# Must be async so that we can construct our value holder.
@pytest.mark.asyncio
async def test_chat_input_client(capsys, monkeypatch):
    value_holder = util.AsyncValueHolder()

    async def mock_ainput(*args, **kwargs):
        return await value_holder.get()

    monkeypatch.setattr("dolor.clients.chat.ainput", mock_ainput)

    client = ChatInputTest(value_holder=value_holder, name="username")
    await client.start()

    out, err = capsys.readouterr()

    assert err == ""

    assert out == (
        "GameInfo: game info\n"
        "Chat: chat\n"
    )

    assert client.create_packet(serverbound.ChatMessagePacket, message="input") in client.sent_packets
