#!/usr/bin/env python3

import dolor
from dolor.client import packet_listener
from dolor.packets import *

import config

class MyClient(dolor.Client):
    @packet_listener(clientbound.UpdateHealthPacket)
    async def respawn(self, p):
        print(p)
        if p.health <= 0:
            await self.write_packet(serverbound.ClientStatusPacket(
                action = dolor.enums.Action.Respawn,
            ))

if __name__ == "__main__":
    c = MyClient("1.15.2", "localhost",
        username = config.username,
        password = config.password,
    )

    c.run()