from dolor import *

from .util import client_test

@client_test
class StatusClientTest(Client):
    received_data = (
        # Pong packet (can't get the payload correct here since it requires the current time).
        b"\x09" + b"\x01" + b"\x00" * 8 +

        # Response packet.
        b"\x68" + b"\x00" + b'\x66{"version":{"name":"1.12.2","protocol":340},"players":{"max":20,"online":0},"description":{"text":""}}'
    )

    async def on_start(self):
        response, _ = await self.status()

        assert response.version               == "1.12.2"
        assert response.players.max           == 20
        assert response.players.online        == 0
        assert response.description.flatten() == ""

        assert self.sent_data.startswith(
            # Handshake packet.
            b"\x0B" + b"\x00" + b"\xD4\x02" + b"\x04test" + b"\x63\xDD" + b"\x01" +

            # Request packet.
            b"\x01" + b"\x00"

            # Cannot test ping packet since it requires the current time.
        )
