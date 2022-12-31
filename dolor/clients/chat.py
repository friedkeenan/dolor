r""":class:`~.Client`\s that handle :class:`~.Chat.Chat` messages."""

import pak
from aioconsole import aprint, ainput

from ..packets import serverbound, clientbound
from .client import Client

__all__ = [
    "ChatClient",
]

class ChatClient(Client):
    """A :class:`~.Client` for interacting with the chat.

    Incoming messages are printed, and outgoing messages may be sent
    if enabled with :attr:`send_input`.

    :meta no-undoc-members:

    Parameters
    ----------
    *args, **kwargs
        Forwarded to :class:`~.Client`.

    Attributes
    ----------
    send_input : :class:`bool`
        Whether input should be polled and sent to the :class:`~.Server`.

    Examples
    --------
    ::

        import dolor

        class MyClient(dolor.clients.ChatClient):
            # We want to be able to send our input to the server.
            send_input = True
    """

    send_input = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.send_input:
            self.register_packet_listener(self._chat_input_loop, clientbound.JoinGamePacket)

    @pak.packet_listener(clientbound.ChatMessagePacket)
    async def _on_chat_message(self, packet):
        await aprint(f"{packet.position.name}: {packet.message.flatten()}")

    async def _chat_input_loop(self, packet):
        while not self.is_closing():
            message = await ainput()

            await self.write_packet(
                serverbound.ChatMessagePacket,

                message = message,
            )
