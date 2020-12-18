import asyncio

from . import connection
from .packet_handler import packet_listener, PacketHandler
from .versions import Version
from .types import Chat
from .packets import PacketContext, ServerboundPacket, serverbound, clientbound

class Server(PacketHandler):
    class Connection(connection.Connection):
        def __init__(self, server, reader, writer):
            print("booya")

            self.ctx = PacketContext(Version(None))

            super().__init__(ServerboundPacket)

            self.server = server
            self.reader = reader
            self.writer = writer

            self.should_listen_sequentially = True

    def __init__(self, version, address, port=25565, *,
        lang_file = None,
    ):
        version = Version(version, check_supported=True)

        self.address = address
        self.port    = port

        self.connections = []

        if lang_file is not None:
            Chat.Chat.load_translations(lang_file)

        super().__init__()

    async def new_connection(self, reader, writer):
        c = self.Connection(self, reader, writer)
        self.connections.append(c)

        while self.srv.is_serving():
            if not await self.listen_step(c)
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

    @packet_listener(serverbound.LoginStartPacket)
    async def _on_login_start(self, c, p):
        print(c, p)
