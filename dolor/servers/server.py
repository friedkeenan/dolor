import asyncio
import aiohttp
import base64
import uuid

from .. import util
from .. import enums
from .. import encryption
from .. import connection
from ..packet_handler import packet_listener, PacketHandler
from ..versions import Version
from ..types import Chat
from ..packets import PacketContext, ServerboundPacket, serverbound, clientbound

class Server(PacketHandler):
    session_server = "https://sessionserver.mojang.com/session/minecraft"

    class Connection(connection.Connection):
        def __init__(self, server, reader, writer):
            self.ctx = PacketContext(Version(None))

            super().__init__(ServerboundPacket)

            self.server = server
            self.reader = reader
            self.writer = writer

            self.should_listen_sequentially = True

            self.name = None
            self.uuid = None

        async def disconnect(self, reason):
            if not isinstance(reason, Chat.Chat):
                reason = Chat.Chat(reason)

            if self.current_state == enums.State.Login:
                packet = clientbound.DisconnectLoginPacket
            else:
                packet = clientbound.DisconnectPlayPacket

            await self.write_packet(packet,
                reason = reason,
            )

            self.close()
            # TODO: Should we wait for the connection to be closed?
            await self.wait_closed()

        def __repr__(self):
            return f"{type(self).__name__}({repr(self.name)}, {repr(self.uuid)})"

    def __init__(self, version, address, port=25565, *,
        lang_file = None,

        max_players = 20,
        description = None,
        favicon     = None,

        comp_threshold = 256,
    ):
        self.version = Version(version, check_supported=True)

        self.address = address
        self.port    = port

        self.private_key = None
        self.public_key  = None

        self.srv         = None
        self.connections = []

        if lang_file is not None:
            Chat.Chat.load_translations(lang_file)

        self.max_players = max_players

        if not isinstance(description, Chat.Chat):
            description = Chat.Chat(description)

        if favicon is not None:
            if util.is_pathlike(favicon):
                with open(favicon, "rb") as f:
                    favicon = f.read()

            favicon = base64.encodebytes(favicon).replace(b"\n", b"")
            favicon = f"data:image/png;base64,{favicon.decode('utf-8')}"

        self.description = description or Chat.default()
        self.favicon     = favicon

        self.comp_threshold = comp_threshold

        super().__init__()

    async def send_server_hash(self, c, server_hash):
        async with aiohttp.ClientSession() as s:
            async with s.get(
                f"{self.session_server}/hasJoined?username={c.name}&serverId={server_hash}",
            ) as resp:
                if resp.status == 204:
                    return False

                # TODO: Verify signature?

                data   = await resp.json()
                c.uuid = uuid.UUID(hex=data["id"])

                return True

    async def new_connection(self, reader, writer):
        c = self.Connection(self, reader, writer)
        self.connections.append(c)

        while self.srv.is_serving():
            if not await self.listen_step(c):
                self.connections.remove(c)

                return

    async def connection_task(self, c):
        print("Logged in:" c)

        # TODO: Fill this out I guess
        await c.write_packet(clientbound.JoinGamePacket)

    async def main_task(self):
        while self.is_serving():
            await asyncio.sleep(1)

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
        return self.srv is not None and self.srv.is_serving()

    def close(self):
        if self.srv is not None:
            self.srv.close()

    async def wait_closed(self):
        await self.srv.wait_closed()

    async def start(self):
        self.private_key, self.public_key = encryption.gen_private_public_keys()

        self.srv = await asyncio.start_server(self.new_connection, self.address, self.port)

        async with self.srv:
            await self.main_task()

    def run(self):
        try:
            asyncio.run(self.start())
        except KeyboardInterrupt:
            self.close()

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
                    "online": len(self.connections),
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
            await c.disconnect({
                "translate": "multiplayer.disconnect.outdated_client",
                "with":      [self.version.name],
            })

            return

        c.name = p.name

        c.verify_token = encryption.gen_verify_token()

        await c.write_packet(clientbound.EncryptionRequestPacket,
            server_id    = "",
            public_key   = self.public_key,
            verify_token = c.verify_token,
        )

    @packet_listener(serverbound.EncryptionResponsePacket)
    async def _on_encryption_response(self, c, p):
        shared_secret, verify_token = encryption.decrypt_secret_and_token(self.private_key, p.shared_secret, p.verify_token)

        if verify_token != c.verify_token:
            await c.disconnect({
                "translate": "multiplayer.disconnect.generic",
            })

            return

        del c.verify_token

        server_hash = encryption.gen_server_hash("", shared_secret, self.public_key)

        if not await self.send_server_hash(c, server_hash):
            await c.disconnect({
                "translate": "multiplayer.disconnect.unverified_username",
            })

            return

        cipher = encryption.gen_cipher(shared_secret)

        c.reader = encryption.EncryptedFileObject(c.reader, cipher.decryptor(), None)
        c.writer = encryption.EncryptedFileObject(c.writer, None, cipher.encryptor())

        await c.write_packet(clientbound.SetCompressionPacket,
            threshold = self.comp_threshold,
        )

        c.comp_threshold = self.comp_threshold

        await c.write_packet(clientbound.LoginSuccessPacket,
            uuid     = c.uuid,
            username = c.name,
        )

        c.current_state = enums.State.Play

        await self.connection_task(c)
