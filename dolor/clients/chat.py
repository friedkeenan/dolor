from aioconsole import aprint, ainput

from ..packet_handler import packet_listener
from ..packets import serverbound, clientbound
from .client import Client

class ChatClient(Client):
    send_input = False

    @packet_listener(clientbound.ChatMessagePacket)
    async def _on_chat_message(self, p):
        await aprint(p.data.flatten())

    @packet_listener(clientbound.JoinGamePacket)
    async def _input_loop(self, p):
        while self.send_input and not self.is_closing():
            message = await ainput()

            await self.write_packet(serverbound.ChatMessagePacket,
                message = message,
            )
