#!/usr/bin/env python3

import argparse
from aioconsole import aprint

import dolor
from dolor.packets import clientbound, serverbound

import config

class MyClient(dolor.clients.ChatClient, dolor.clients.RespawnClient):
    send_input = True

    @dolor.packet_listener(clientbound.RespawnPacket)
    async def on_respawn(self, p):
        await aprint(p)

class MyServer(dolor.servers.ChatServer):
    pass

def test_client():
    c = MyClient("1.16.4", "localhost",
        lang_file = "en_us.json",
        username  = config.username,
        password  = config.password,
    )

    c.run()

def test_server():
    s = MyServer("1.16.4", "localhost", 25566,
        lang_file = "en_us.json",
    )

    s.run()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("--test", "-t", default="client")

    args = parser.parse_args()

    if args.test == "client":
        test_client()
    elif args.test == "server":
        test_server()
