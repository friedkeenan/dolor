#!/usr/bin/env python3

import dolor
from dolor.packets import clientbound, serverbound

import config

class MyClient(dolor.Client):
    @dolor.packet_listener(clientbound.ChatMessagePacket)
    async def on_message(self, p):
        print(p.data.flatten())

    @dolor.packet_listener(clientbound.UpdateHealthPacket)
    async def respawn(self, p):
        print(p)

        if p.health <= 0:
            await self.write_packet(serverbound.ClientStatusPacket,
                action = dolor.enums.Action.Respawn,
            )

            await self.write_packet(serverbound.ChatMessagePacket,
                message = "Poop",
            )

    @dolor.packet_listener(clientbound.RespawnPacket)
    async def on_respawn(self, p):
        print(p)

if __name__ == "__main__":
    c = MyClient("1.16.4", "localhost",
        username  = config.username,
        password  = config.password,
        lang_file = "en_us.json",
    )

    c.run()
