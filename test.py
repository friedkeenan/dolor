#!/usr/bin/env python3

import dolor
from dolor.client import packet_listener

import config

class MyClient(dolor.Client):
    @packet_listener(0x21)
    async def keep_alive(self, p):
        print(p)

if __name__ == "__main__":
    c = MyClient("1.15.2", "localhost",
        username = config.username,
        password = config.password,
    )

    c.run()