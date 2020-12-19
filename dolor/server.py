import asyncio
import base64

from . import util
from . import connection
from .packet_handler import packet_listener, PacketHandler
from .versions import Version
from .types import Chat
from .packets import PacketContext, ServerboundPacket, serverbound, clientbound

class Server(PacketHandler):
    class Connection(connection.Connection):
        def __init__(self, server, reader, writer):
            self.ctx = PacketContext(Version(None))

            super().__init__(ServerboundPacket)

            self.server = server
            self.reader = reader
            self.writer = writer

            self.should_listen_sequentially = True

    def __init__(self, version, address, port=25565, *,
        lang_file = None,

        max_players = 20,
        description = None,
        favicon     = None,
    ):
        self.version = Version(version, check_supported=True)

        self.address = address
        self.port    = port

        self.srv         = None
        self.connections = []

        if lang_file is not None:
            Chat.Chat.load_translations(lang_file)

        self.max_players    = max_players
        self.online_players = 0

        if not isinstance(description, Chat.Chat):
            description = Chat.Chat(description)

        if favicon is not None:
            if util.is_pathlike(favicon):
                with open(favicon, "rb") as f:
                    favicon = f.read()

            favicon = base64.encodebytes(favicon).replace(b"\n", b"")
            favicon = f"data:image/png;base64,{favicon}"

        self.description = description or Chat.default()
        self.favicon     = favicon

        super().__init__()

    async def new_connection(self, reader, writer):
        c = self.Connection(self, reader, writer)
        self.connections.append(c)

        while self.srv.is_serving():
            if not await self.listen_step(c):
                self.connections.remove(c)

                return

    async def listen_step(self, c):
        p = await c.read_packet()
        if p is None:
            return False

        tasks = []
        for func, checker in self.packet_listeners.items():
            if checker(c, p):
                if c.should_listen_sequentially:
                    tasks.append(func(c, p))
                else:
                    asyncio.create_task(func(c, p))

        if c.should_listen_sequentially:
            await asyncio.gather(*tasks)

        return True

    def is_serving(self):
        return self.srv.is_serving()

    def close(self):
        self.srv.close()

    async def wait_closed(self):
        await self.srv.wait_closed()

    async def start(self):
        self.srv = await asyncio.start_server(self.new_connection, self.address, self.port)

        await self.srv.serve_forever()

    def run(self):
        try:
            asyncio.run(self.start())
        except KeyboardInterrupt:
            pass

    # Default packet listeners

    @packet_listener(serverbound.HandshakePacket)
    async def _on_handshake(self, c, p):
        c.ctx           = PacketContext(Version(p.proto_version))
        c.current_state = p.next_state

    @packet_listener(serverbound.RequestPacket)
    async def _on_request(self, c, p):
        await c.write_packet(clientbound.ResponsePacket,
            response = clientbound.ResponsePacket.Response.Response(
                version = self.version,

                players = {
                    "max":    self.max_players,
                    "online": self.online_players,
                    "sample": [],
                },

                description = self.description,
                favicon     = self.favicon,
            ),
        )

    @packet_listener(serverbound.PingPacket)
    async def _on_ping(self, c, p):
        await c.write_packet(clientbound.PongPacket,
            payload = p.payload,
        )

    @packet_listener(serverbound.LoginStartPacket)
    async def _on_login_start(self, c, p):
        if c.ctx.version != self.version:
            await c.write_packet(clientbound.DisconnectLoginPacket,
                reason = Chat.Chat({
                    "translate": "multiplayer.disconnect.outdated_client",
                    "with": [self.version.name],
                }),
            )

            c.close()
            await c.wait_closed()

        print(c, p)
