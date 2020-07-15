#!/usr/bin/env python3

import socket
import json
import base64
import dolor

class MyClient(dolor.Client):
    async def on_start(self):
        resp, ping = await self.status()
        print(resp, ping)

if __name__ == "__main__":
    c = MyClient("1.15.2", "avatarmc.com")
    c.run()