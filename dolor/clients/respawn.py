from .. import enums
from ..packet_handler import packet_listener
from ..packets import serverbound, clientbound
from .client import Client

class RespawnClient(Client):
    @packet_listener(clientbound.UpdateHealthPacket)
    async def _respawn(self, p):
        if p.health <= 0:
            await self.write_packet(serverbound.ClientStatusPacket,
                action = enums.Action.Respawn,
            )
