#!/usr/bin/env python3

import socket
import json
import base64
from dolor.packets import *

with open("favicon.png", "rb") as f:
    favicon = base64.encodebytes(f.read()).decode().replace("\n", "")

ping_response = {
    "version": {
        "name": "1.12.2",
        "protocol": 340
    },
    "players": {
        "max": 150,
        "online": 0,
        "sample": []
    },
    "description": {
        "bold": True,
        "text": "This is a test"
    },
    "favicon": f"data:image/png;base64,{favicon}"
}

def handle_ping(sock):
    s = sock.accept()[0]
    buf = s.makefile("rb")

    p = serverbound.HandshakePacket(buf)
    print(p)

    if p.next_state.value != 1:
        raise ValueError("Fuck off")

    p = serverbound.RequestPacket(buf)
    print(p)

    p = clientbound.ResponsePacket(response=ping_response)
    s.send(bytes(p))

    p = serverbound.PingPacket(buf)
    print(p)

    p = clientbound.PongPacket(payload=p.payload)
    s.send(bytes(p))

    buf.close()
    s.close()

if __name__ == "__main__":
    sock = socket.socket()
    sock.bind(("localhost", 25565))
    sock.listen(5)

    while True:
        handle_ping(sock)

    sock.close()