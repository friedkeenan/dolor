import asyncio
import aiohttp
import base64
import uuid
import time
from aioconsole import aprint

from .. import util
from .. import encryption
from ..packet_handler import packet_listener, PacketHandler
from ..versions import Version
from ..types import Chat
from ..packets import PacketContext, ServerboundPacket, serverbound, clientbound
from . import connections

def connection_task(func):
    """Decorator for connection tasks within a class."""

    func._connection_task = True

    return func

class Server(PacketHandler):
    session_server = "https://sessionserver.mojang.com/session/minecraft"

    Connection = connections.Connection

    def __init__(self, version, address, port=25565, *,
        lang_file = None,

        max_players = 20,
        description = None,
        favicon     = None,

        offline        = False,
        comp_enabled   = True,
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

        if favicon is not None:
            if util.is_pathlike(favicon):
                with open(favicon, "rb") as f:
                    favicon = f.read()

            favicon = base64.encodebytes(favicon).replace(b"\n", b"")
            favicon = f"data:image/png;base64,{favicon.decode('utf-8')}"

        self.description = description or Chat.default()
        self.favicon     = favicon

        self.offline        = offline
        self.comp_enabled   = comp_enabled
        self.comp_threshold = comp_threshold

        self.connection_tasks = []
        self.register_intrinsic_connection_tasks()

        super().__init__()

    def register_connection_task(self, func):
        """
        Registers a packet listener.

        func is a coroutine function.
        """
        if not asyncio.iscoroutinefunction(func):
            raise TypeError(f"Connection task {func.__name__} isn't a coroutine function")

        self.connection_tasks.append(func)

    def unregister_connection_task(self, func):
        """Unregisters a connection task."""

        self.connection_tasks.remove(func)

    def external_connection_task(self, func):
        """Decorator for external connection tasks."""

        self.register_connection_task(func)

        return func

    def register_intrinsic_connection_tasks(self):
        for attr in dir(self):
            func = getattr(self, attr)

            # If the function was decorated with
            # the connection_task function, then
            # it will have the _connection_task
            # attribute, which will also be true
            if hasattr(func, "_connection_task") and func._connection_task:
                self.register_connection_task(func)

    def safe_connection_func(self, task):
        async def safe(c, *args, **kwargs):
            try:
                await task(c, *args, **kwargs)
            except Exception as e:
                await c.disconnect(e)

        return safe

    async def listen_to_packet(self, c, p, *, outgoing):
        listeners = self.listeners_for_packet(c, p, outgoing=outgoing)
        listeners = [self.safe_connection_func(x) for x in listeners]

        if c.should_listen_sequentially:
            await asyncio.gather(*(x(c, p) for x in listeners))
        else:
            for func in listeners:
                c.create_task(func(c, p))

    async def listen(self, c):
        while self.is_serving() and not c.is_closing():
            try:
                p = await c.read_packet()
            except Exception as e:
                await c.disconnect(e)

                break

            if p is None:
                break

            await self.listen_to_packet(c, p, outgoing=False)

        try:
            await asyncio.wait_for(asyncio.gather(*c.tasks), 1)
        except asyncio.TimeoutError:
            for task in c.tasks:
                task.cancel()

    async def new_connection(self, reader, writer):
        c = self.Connection(self, reader, writer)

        async with c:
            self.append(c)
            await self.listen(c)
            self.remove(c)

    async def central_connection_task(self, c):
        tasks = [self.safe_connection_func(x) for x in self.connection_tasks]

        await asyncio.gather(*(x(c) for x in tasks))

    async def main_task(self):
        while self.is_serving():
            await asyncio.sleep(1)

    def is_serving(self):
        return self.srv is not None and self.srv.is_serving()

    def close(self):
        if self.srv is not None:
            for c in self.connections:
                c.close()

            self.connections.clear()

            self.srv.close()

    async def wait_closed(self):
        if self.srv is not None:
            await self.srv.wait_closed()

    def __del__(self):
        self.close()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, exc_tb):
        self.close()
        await self.wait_closed()

    def append(self, c):
        self.connections.append(c)

    def remove(self, c):
        self.connections.remove(c)

    async def on_start(self):
        await self.main_task()

    async def startup(self):
        self.private_key, self.public_key = encryption.gen_private_public_keys()

        self.srv = await asyncio.start_server(self.new_connection, self.address, self.port)

    async def start(self):
        await self.startup()

        async with self:
            await self.on_start()

    def run(self):
        try:
            asyncio.run(self.start())
        except KeyboardInterrupt:
            self.close()

    @property
    def players(self):
        return [x for x in self.connections if x.is_player]

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

    # Default packet listeners and tasks

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
                    "online": len(self.players),
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

        if len(self.players) >= self.max_players:
            await c.disconnect({
                "translate": "multiplayer.disconnect.server_full",
            })

        if p.name in (x.name for x in self.connections):
            await c.disconnect({
                "translate": "multiplayer.disconnect.name_taken",
            })

            return

        c.name = p.name

        if not self.offline:
            c.verify_token = encryption.gen_verify_token()

            await c.write_packet(clientbound.EncryptionRequestPacket,
                server_id    = "",
                public_key   = self.public_key,
                verify_token = c.verify_token,
            )
        else:
            if self.comp_enabled:
                await c.set_compression(self.comp_threshold)

            await c.login_success()

    @packet_listener(serverbound.EncryptionResponsePacket)
    async def _on_encryption_response(self, c, p):
        shared_secret, verify_token = encryption.decrypt_secret_and_token(self.private_key, p.shared_secret, p.verify_token)
        c.enable_encryption(shared_secret)

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

        if c in self.players:
            await c.disconnect({
                "translate": "multiplayer.disconnect.duplicate_login",
            })

            return

        if self.comp_enabled:
            await c.set_compression(self.comp_threshold)

        await c.login_success()

    @connection_task
    async def _join_game_task(self, c):
        await aprint("Logged in:", c)

        # TODO: Fill this out I guess
        await c.write_packet(clientbound.JoinGamePacket)

    @connection_task
    async def _keep_alive_task(self, c):
        timeout = 25
        sleep   = 5

        while not c.is_closing():
            await asyncio.sleep(sleep)

            keep_alive_id = int(time.time() * 1000)

            await c.write_packet(clientbound.KeepAlivePacket,
                keep_alive_id = keep_alive_id,
            )

            try:
                p = await asyncio.wait_for(c.read_packet(serverbound.KeepAlivePacket), timeout)
            except asyncio.TimeoutError:
                await c.disconnect({
                    "translate": "disconnect.timeout",
                })

                return

            if p is None:
                return

            if p.keep_alive_id != keep_alive_id:
                await c.disconnect({
                    "translate": "disconnect.timeout",
                })

                return
