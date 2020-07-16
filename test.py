#!/usr/bin/env python3

import dolor
import config

c = dolor.Client("1.15.2", "localhost",
    username = config.username,
    password = config.password,
)

@c.packet_listener(0x21)
async def test(p):
    print(p)

if __name__ == "__main__":
    c.run()