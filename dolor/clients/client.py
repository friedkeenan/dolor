import asyncio
import aiohttp
import time
from aioconsole import aprint

from .. import enums
from .. import util
from .. import encryption
from .. import connection
from ..packet_handler import packet_listener, PacketHandler
from ..versions import Version
from ..types import Chat
from ..packets import PacketContext, serverbound, clientbound
from ..yggdrasil import AuthenticationToken

class Client(connection.Connection, PacketHandler):
    session_server = "https://sessionserver.mojang.com/session/minecraft"

    def __init__(self, version, address, port=25565, *,
        lang_file = None,

        access_token = None,
        client_token = None,
        username     = None,
        password     = None,

        name = None,
    ):
        version  = Version(version, check_supported=True)
        self.ctx = PacketContext(version)

        self.address = address
        self.port    = port

        self.authenticated = False
        self.auth_token = AuthenticationToken(
            access_token = access_token,
            client_token = client_token,
            username     = username,
            password     = password,
        )

        self.name = name

        if lang_file is not None:
            Chat.Chat.load_translations(lang_file)

        self.should_listen_sequentially = True
        self.tasks = []

        # TODO: Figure out a way to do this with super
        connection.Connection.__init__(self, clientbound)
        PacketHandler.__init__(self)

    def register_packet_listener(self, *args, outgoing=False):
        super().register_packet_listener(*args, outgoing=outgoing)

    def create_task(self, coro):
        """Internal function used to ensure that all listeners complete."""

        real_task = asyncio.create_task(coro)
        self.tasks.append(real_task)

        async def task():
            try:
                await real_task
            finally:
                self.tasks.remove(real_task)

        return asyncio.create_task(task())

    async def listen_to_packet(self, p, *, outgoing):
        listeners = self.listeners_for_packet(self, p, outgoing=outgoing)

        if self.should_listen_sequentially:
            await asyncio.gather(*(x(p) for x in listeners))
        else:
            for func in listeners:
                self.create_task(func(p))

    async def write_packet(self, *args, **kwargs):
        p = await super().write_packet(*args, **kwargs)

        await self.listen_to_packet(p, outgoing=True)

        return p

    async def listen(self):
        while not self.is_closing():
            p = await self.read_packet()
            if p is None:
                break

            await self.listen_to_packet(p, outgoing=False)

        try:
            await asyncio.wait_for(asyncio.gather(*self.tasks), 1)
        except asyncio.TimeoutError:
            for task in self.tasks:
                task.cancel()

    async def on_start(self):
        await self.login()

    async def startup(self):
        self.reader, self.writer = await asyncio.open_connection(self.address, self.port)

    async def start(self):
        await self.startup()

        async with self:
            await self.on_start()

    def run(self):
        try:
            asyncio.run(self.start())
        except KeyboardInterrupt:
            self.close()

    async def auth(self, **kwargs):
        await self.auth_token.ensure(**kwargs)
        self.authenticated = True

        if self.name is None:
            self.name = self.auth_token.profile.name

    async def send_server_hash(self, server_hash):
        async with aiohttp.ClientSession() as s:
            async with s.post(f"{self.session_server}/join",
                json = {
                    "accessToken":     self.auth_token.access_token,
                    "selectedProfile": self.auth_token.profile.id,
                    "serverId":        server_hash,
                },
                headers = {"content-type": "application/json"},
            ) as resp:
                if resp.status != 204:
                    raise ValueError(f"Invalid status code from session server: {resp.status}")

    async def status(self):
        if self.current_state != enums.State.Handshaking:
            raise ValueError(f"Invalid state: {self.current_state}")

        await self.write_packet(serverbound.HandshakePacket,
            proto_version  = self.ctx.version.proto,
            server_address = self.address,
            server_port    = self.port,
            next_state     = enums.State.Status,
        )

        self.current_state = enums.State.Status

        await self.write_packet(serverbound.RequestPacket)
        resp = await self.read_packet()

        await self.write_packet(serverbound.PingPacket,
            payload = int(time.time() * 1000),
        )
        pong = await self.read_packet()

        self.close()

        return resp.response, int(time.time() * 1000) - pong.payload

    async def login(self):
        if self.current_state != enums.State.Handshaking:
            raise ValueError(f"Invalid state: {self.current_state}")

        if self.name is None:
            # If we don't have a name then we need to get it,
            # so we can't just validate, we need to refresh.
            await self.auth()

        self.should_listen_sequentially = True

        await self.write_packet(serverbound.HandshakePacket,
            proto_version  = self.ctx.version.proto,
            server_address = self.address,
            server_port    = self.port,
            next_state     = enums.State.Login,
        )

        self.current_state = enums.State.Login

        await self.write_packet(serverbound.LoginStartPacket,
            name = self.name,
        )

        await self.listen()

    # Default packet listeners

    @packet_listener(clientbound.DisconnectLoginPacket, clientbound.DisconnectPlayPacket)
    async def _on_disconnect(self, p):
        await aprint("Disconnected:", p.reason.flatten())

        self.close()
        await self.wait_closed()

    @packet_listener(clientbound.EncryptionRequestPacket)
    async def _on_encryption_request(self, p):
        if not self.authenticated:
            await self.auth(try_validate=True)

        shared_secret = encryption.gen_shared_secret()
        server_hash   = encryption.gen_server_hash(p.server_id, shared_secret, p.public_key)

        await self.send_server_hash(server_hash)

        enc_secret, enc_token = encryption.encrypt_secret_and_token(p.public_key, shared_secret, p.verify_token)

        await self.write_packet(serverbound.EncryptionResponsePacket,
            shared_secret = enc_secret,
            verify_token  = enc_token,
        )

        self.enable_encryption(shared_secret)

    @packet_listener(clientbound.SetCompressionPacket)
    async def _on_set_compression(self, p):
        self.comp_threshold = p.threshold

    @packet_listener(clientbound.LoginSuccessPacket)
    async def _on_login_success(self, p):
        self.current_state = enums.State.Play

        self.should_listen_sequentially = False

    @packet_listener(clientbound.KeepAlivePacket)
    async def _on_keep_alive(self, p):
        await self.write_packet(serverbound.KeepAlivePacket,
            keep_alive_id = p.keep_alive_id,
        )
