import asyncio
import aiohttp
import base64
import uuid
import time
from aioconsole import aprint

from .. import util
from .. import enums
from .. import encryption
from .. import connection
from ..packet_handler import packet_listener, PacketHandler
from ..versions import Version
from ..types import Chat, Identifier
from ..packets import PacketContext, serverbound, clientbound

def connection_task(func):
    """Decorator for connection tasks within a class."""

    func._connection_task = True

    return func

class ServerConnection(connection.Connection):
    def __init__(self, server, reader, writer):
        self.ctx = PacketContext(Version(None))

        super().__init__(serverbound)

        self.server = server

        self.reader = reader
        self.writer = writer

        self.should_listen_sequentially = True
        self.tasks = []

        self.central_task = None

        self.name = ""
        self.uuid = uuid.UUID(int=0)

    @property
    def is_player(self):
        return self.current_state == enums.State.Play

    async def disconnect(self, reason):
        if isinstance(reason, Exception):
            reason = f"{type(reason).__name__}: {reason}"

        packet = {
            enums.State.Login: clientbound.DisconnectLoginPacket,
            enums.State.Play:  clientbound.DisconnectPlayPacket,
        }.get(self.current_state)

        if packet is not None:
            try:
                await self.write_packet(packet,
                    reason = reason,
                )
            except:
                pass

        self.close()
        await self.wait_closed()

    async def set_compression(self, threshold):
        await self.write_packet(clientbound.SetCompressionPacket,
            threshold = threshold,
        )

        self.comp_threshold = threshold

    async def login_success(self):
        await self.write_packet(clientbound.LoginSuccessPacket,
            uuid     = self.uuid,
            username = self.name,
        )

        self.current_state              = enums.State.Play
        self.should_listen_sequentially = False

        self.central_task = asyncio.create_task(self.server.central_connection_task(self))

    async def message(self, message, *, position=enums.ChatPosition.Chat, sender=None):
        if sender is None:
            sender = uuid.UUID(int=0)
        else:
            sender = sender.uuid

        await self.write_packet(clientbound.ChatMessagePacket(
            data     = message,
            position = position,
            sender   = sender,
        ))

    def close(self):
        if not self.is_closing():
            super().close()

            if self.central_task is not None:
                self.central_task.cancel()

    async def wait_closed(self):
        if self.is_closing():
            await super().wait_closed()

            if self.central_task is not None:
                # Use asyncio.wait_for?
                await self.central_task

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

    async def write_packet(self, *args, **kwargs):
        p = await super().write_packet(*args, **kwargs)

        await self.server.listen_to_packet(self, p, outgoing=True)

        return p

    def __eq__(self, other):
        return self.uuid == other.uuid

    def __hash__(self):
        return hash(self.uuid)

    def __repr__(self):
        return f"{type(self).__name__}({repr(self.name)}, {repr(self.uuid)})"

class Server(PacketHandler):
    session_server = "https://sessionserver.mojang.com/session/minecraft"

    Connection = ServerConnection

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

    def register_packet_listener(self, *args, outgoing=False):
        super().register_packet_listener(*args, outgoing=outgoing)

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

    def append(self, conn):
        self.connections.append(conn)

    def remove(self, conn):
        # Loop over connections to check identity
        # of connections instead of equality
        for i, c in enumerate(self.connections):
            if c is conn:
                self.connections.pop(i)

    async def startup(self):
        self.private_key, self.public_key = encryption.gen_private_public_keys()

        self.srv = await asyncio.start_server(self.new_connection, self.address, self.port)

    async def on_start(self):
        await self.main_task()

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
        # TODO: Make this all programmatic

        dim_identifier = Identifier.Identifier("minecraft:overworld")

        p = c.create_packet(clientbound.JoinGamePacket,
            entity_id      = 1,
            game_mode      = enums.GameMode.Survival,
            prev_game_mode = enums.GameMode.Invalid,
            world_names    = [dim_identifier],
            world_name     = dim_identifier,
            max_players    = self.max_players,
            view_distance  = 10,
        )

        if c.ctx.version < "20w21a":
            pass
        elif c.ctx.version < "1.16.2-pre3":
            p.dimension = dim_identifier
        else:
            p.dimension.name             = dim_identifier
            p.dimension.shrunk           = False
            p.dimension.coordinate_scale = 1.0

            p.dimension.infiniburn = "minecraft:infiniburn_overworld"
            p.dimension.effects    = dim_identifier

            if c.ctx.version < "1.16-pre3":
                p.dimension_codec["dimension"] = [{
                    "key":     dim_identifier,
                    "element": dim_identifier,
                }]
            elif c.ctx.version < "20w28a":
                p.dimension_codec["dimension"] = [p.dimension]
            else:
                p.dimension_codec["minecraft:dimension_type"] = {
                    "type":  "minecraft:dimension_type",
                    "value": [{
                        "name":    dim_identifier,
                        "id":      0,
                        "element": p.dimension,
                    }],
                }

                p.dimension_codec["minecraft:worldgen/biome"] = {
                    "type":  "minecraft:worldgen/biome",
                    "value": [{
                        "name": "minecraft:plains",
                        "id":   1,

                        "element": {
                            "category":      "plains",
                            "precipitation": "rain",
                            "downfall":      0.4000000059604645,
                            "temperature":   0.800000011920929,
                            "depth":         0.125,
                            "scale":         0.05000000074505806,

                            "effects": {
                                "sky_color":       0x78a7ff,
                                "fog_color":       0xc0d8ff,
                                "water_color":     0x3f76e4,
                                "water_fog_color": 0x050533,

                                "mood_sound": {
                                    "sound":               "minecraft:ambient.cave",
                                    "offset":              2.0,
                                    "tick_delay":          6000,
                                    "block_search_extent": 8,
                                },
                            },
                        }
                    }],
                }

        await c.write_packet(p)
        await c.write_packet(clientbound.PlayerPositionAndLook)

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
