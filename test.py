#!/usr/bin/env python3

import dolor
from dolor.packets import clientbound, serverbound
from aioconsole import aprint

import config

class MyClient(dolor.clients.ChatClient, dolor.clients.RespawnClient):
    should_send_input = True

    @dolor.packet_listener(clientbound.RespawnPacket)
    async def on_respawn(self, p):
        await aprint(p)

if __name__ == "__main__":
    c = MyClient("1.16.4", "localhost",
        lang_file = "en_us.json",
        username  = config.username,
        password  = config.password,
    )

    c.run()
