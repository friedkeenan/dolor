from .. import enums
from ..packets import serverbound
from ..packet_handler import packet_listener
from .server import Server

class ChatServer(Server):
    async def distribute_message(self, message, *, position=enums.ChatPosition.Chat, sender=None):
        for p in self.players:
            await p.message(message, position=position, sender=sender)

    async def handle_command(self, sender, command):
        pass

    @packet_listener(serverbound.ChatMessagePacket)
    async def _on_chat_message(self, c, p):
        if p.message.startswith("/"):
            await self.handle_command(c, p.message[1:])

            return

        await self.distribute_message({
            "translate": "chat.type.text",
            "with": [c.name, p.message],
        }, sender=c)
