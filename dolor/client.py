import asyncio
import aiohttp
import time
import zlib
import io

from . import enums
from . import util
from . import encryption
from . import common
from .common import packet_listener
from .versions import Version
from .types import VarInt, Chat
from .packets import PacketContext, ClientboundPacket, GenericPacket, serverbound, clientbound
from .yggdrasil import AuthenticationToken

class Client:
    session_server = "https://sessionserver.mojang.com/session/minecraft"

    def __init__(self, version, address, port=25565, *,
        access_token = None,
        client_token = None,
        username     = None,
        password     = None,
        lang_file    = None,
    ):
        version  = Version(version, check_supported=True)
        self.ctx = PacketContext(version)

        self.address = address
        self.port    = port

        self.auth_token = AuthenticationToken(
            access_token = access_token,
            client_token = client_token,
            username     = username,
            password     = password,
        )

        if lang_file is not None:
            Chat.Chat.load_translations(lang_file)

        self.current_state = enums.State.Handshaking

        self.closed     = True
        self.transport  = None
        self.read_queue = None
        self.decryptor  = None
        self.encryptor  = None

        self.comp_threshold = 0

        self.should_listen_sequentially = False

        self.packet_listeners = {}
        for attr in dir(self):
            tmp = getattr(self, attr)

            # If the function was decorated with
            # the packet_listener function, then
            # it will have the _checkers attribute
            if hasattr(tmp, "_checkers"):
                self.register_packet_listener(tmp, *tmp._checkers)

    @property
    def ctx(self):
        return self._ctx

    @ctx.setter
    def ctx(self, value):
        self._ctx = value

        try:
            self.packet_info = common.gen_packet_info(self.current_state, ClientboundPacket, ctx=value)
        except AttributeError:
            pass

    @property
    def current_state(self):
        return self._current_state

    @current_state.setter
    def current_state(self, value):
        self._current_state = value

        try:
            self.packet_info = common.gen_packet_info(value, ClientboundPacket, ctx=self.ctx)
        except AttributeError:
            pass

    def protocol_factory(self):
        return common.ClientServerProtocol(self)

    def connection_made(self, transport):
        self.closed = False

    def connection_lost(self, exc):
        self.close()

        if exc is not None:
            raise exc

    def data_received(self, data):
        self.read_queue.put_nowait(data)

    def close(self):
        if not self.closed:
            self.closed = True

            if not self.transport.is_closing():
                self.transport.write_eof()
                self.transport.close()

    def abort(self):
        self.transport.abort()
        self.close()

    def to_real_packet_checker(self, checker):
        if isinstance(checker, type):
            # Packet class
            return lambda x: isinstance(x, checker)
        elif isinstance(checker, int):
            # Packet id
            return lambda x: (x.get_id(ctx=self.ctx) == checker)

        return checker

    def join_checkers(self, first, second):
        return lambda x: (first(x) or second(x))

    def register_packet_listener(self, func, *checkers):
        """
        Registers a packet listener.

        func is a coroutine function and each
        checker is either a packet class, a packet
        id, or a function that returns whether
        the listener should be called.
        """

        if not asyncio.iscoroutinefunction(func):
            raise TypeError(f"Packet listener {func.__name__} isn't a coroutine function")

        real_checker = None
        for c in checkers:
            real_c = self.to_real_packet_checker(c)

            if real_checker is None:
                real_checker = real_c
            else:
                real_checker = self.join_checkers(real_checker, real_c)

        self.packet_listeners[func] = real_checker

    def unregister_packet_listener(self, func):
        """Unregisters a packet listener."""

        self.packet_listeners.pop(func)

    def external_packet_listener(self, *checkers):
        """Decorator for external packet listeners."""

        def dec(func):
            self.register_packet_listener(func, *checkers)

            return func

        return dec

    async def read_packet(self, *, timeout=None):
        """
        Reads a packet from the server.

        If timeout is None, it will return
        None if the connection gets closed,
        otherwise it will only return once
        it receives a packet.

        Otherwise, it will try to return
        the packet before it times out no
        matter what.
        """

        while not self.closed:
            if timeout is not None:
                data = await asynio.wait_for(self.read_queue.get(), timeout)
            else:
                try:
                    data = await asyncio.wait_for(self.read_queue.get(), 1)
                except asyncio.TimeoutError:
                    continue

            data = io.BytesIO(data)

            if self.comp_threshold > 0:
                data_len = VarInt.unpack(data, ctx=self.ctx)

                if data_len > 0:
                    if data_len < self.comp_threshold:
                        self.close()

                        raise ValueError(f"Invalid data length ({data_len}) for compression threshold ({self.comp_threshold})")

                    data = io.BytesIO(zlib.decompress(data.read(), bufsize=data_len))

            id         = VarInt.unpack(data, ctx=self.ctx)
            pack_class = self.packet_info.get(id)

            if pack_class is None:
                pack_class = GenericPacket(id)

            return pack_class.unpack(data, ctx=self.ctx)

        return None

    async def write_packet(self, packet, **kwargs):
        """
        Writes a packet to the server.

        packet can be either a Packet object,
        or it can be a Packet class, and then
        the sent packet will be made using that
        class and the keyword arguments.

        packet being a Packet class is preferred
        because then the context will be correctly
        passed to the sent packet.
        """

        if isinstance(packet, type):
            packet = packet(ctx=self.ctx, **kwargs)

        data = packet.pack(ctx=self.ctx)

        if self.comp_threshold > 0:
            data_len = 0

            if len(data) > self.comp_threshold:
                data_len = len(data)
                data     = zlib.compress(data)

            data = VarInt.pack(data_len, ctx=self.ctx) + data

        data = VarInt.pack(len(data), ctx=self.ctx) + data

        if self.encryptor is not None:
            data = self.encryptor.update(data)

        self.transport.write(data)

    def default_packet(self, pack_class):
        """
        Utility method for getting the default
        of a packet with the correct context.
        """

        return pack_class(ctx=self.ctx)

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

    async def start(self):
        self.read_queue = asyncio.Queue()

        self.transport, _ = await asyncio.get_running_loop().create_connection(self.protocol_factory, self.address, self.port)

        await self.on_start()

    async def listen(self):
        while not self.closed:
            p = await self.read_packet()
            if p is None:
                return

            tasks = []
            for func, checker in self.packet_listeners.items():
                if checker(p):
                    if self.should_listen_sequentially:
                        tasks.append(func(p))
                    else:
                        asyncio.create_task(func(p))

            if self.should_listen_sequentially:
                await asyncio.gather(*tasks)

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

        await self.auth_token.ensure()

        self.should_listen_sequentially = True

        await self.write_packet(serverbound.HandshakePacket,
            proto_version = self.ctx.version.proto,
            server_address = self.address,
            server_port = self.port,
            next_state = enums.State.Login,
        )

        self.current_state = enums.State.Login

        await self.write_packet(serverbound.LoginStartPacket,
            name = self.auth_token.profile.name,
        )

        await self.listen()

    async def on_start(self):
        await self.login()

    def run(self):
        try:
            asyncio.run(self.start())
        except KeyboardInterrupt:
            pass

    # Default packet listeners

    @packet_listener(clientbound.DisconnectLoginPacket, clientbound.DisconnectPlayPacket)
    async def _on_disconnect(self, p):
        print("Disconnected:", p.reason.flatten())

    @packet_listener(clientbound.EncryptionRequestPacket)
    async def _on_encryption_request(self, p):
        shared_secret = encryption.gen_shared_secret()
        server_hash   = encryption.gen_server_hash(p.server_id, shared_secret, p.public_key)

        await self.send_server_hash(server_hash)

        enc_secret, enc_token = encryption.encrypt_secret_and_token(p.public_key, shared_secret, p.verify_token)

        await self.write_packet(serverbound.EncryptionResponsePacket,
            shared_secret = enc_secret,
            verify_token  = enc_token,
        )

        cipher = encryption.gen_cipher(shared_secret)
        self.decryptor = cipher.decryptor()
        self.encryptor = cipher.encryptor()

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
