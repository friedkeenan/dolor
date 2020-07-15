#!/usr/bin/env python3

import dolor
import config

class MyClient(dolor.Client):
    async def on_start(self):
        print(await self.login())

if __name__ == "__main__":
    c = MyClient("1.15.2", "localhost",
        username = config.username,
        password = config.password,
    )

    c.run()