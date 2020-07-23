import asyncio
import aiohttp
import io
import zlib
import time
import copy

from . import enums
from . import util
from . import versions
from . import encryption
from . import common
from .types import *
from .packets import *
from .yggdrasil import AuthenticationToken

def packet_listener(*checkers):
    """
    A decorator for packet listeners
    within a Client class.

    checkers is the same as in
    Client.register_packet_listener.
    """

    def dec(func):
        # Set the checkers attribute to be later
        # recognized and registered by the client
        func.checkers = checkers

        return func

    return dec

class Client:
    session_server = "https://sessionserver.mojang.com/session/minecraft"

    def __init__(
        self,
        version,
        address,
        port = 25565,
        *,
        access_token = None,
        client_token = None,
        username = None,
        password = None,
        lang_file = None,
    ):
        if isinstance(version, int):
            proto = version
        else:
            proto = versions.versions.get(version)
            if proto is None:
                raise ValueError("Unsupported Minecraft version! If you know what you're doing, use the raw protocol version instead.")

        self.ctx = PacketContext(proto)

        self.address = address
        self.port = port

        self.auth_token = AuthenticationToken(
            access_token = access_token,
            client_token = client_token,
            username = username,
            password = password,
        )

        if lang_file is not None:
            Chat.Chat.load_translations(lang_file)

        self.current_state = enums.State.Handshaking

        self.closed = True

        self.transport = None
        self.read_queue = None
        self.decryptor = None
        self.encryptor = None

        self.comp_threshold = 0

        self.packet_listeners = {}
        for attr in dir(self):
            tmp = getattr(self, attr)

            # If the function was decorated with
            # the packet_listener function, then
            # it will have the checkers attribute
            if hasattr(tmp, "checkers"):
                self.register_packet_listener(tmp, *tmp.checkers)

    def gen_packet_info(self, state=None):
        if state is None:
            state = self.current_state

        state = {
            enums.State.Handshaking: HandshakingPacket,
            enums.State.Status:      StatusPacket,
            enums.State.Login:       LoginPacket,
            enums.State.Play:        PlayPacket,
        }[state]

        ret = {}
        for c in util.get_subclasses(state) & util.get_subclasses(ClientboundPacket):
            id = c.get_id(self.ctx)
            if id is not None:
                ret[id] = c

        return ret

    @property
    def current_state(self):
        return self._current_state

    @current_state.setter
    def current_state(self, state):
        self._current_state = state
        self.packet_info = self.gen_packet_info()

    def protocol_factory(self):
        return common.Protocol(self)

    def connection_made(self):
        self.closed = False

    def connection_lost(self, exc):
        self.close()

        if exc is not None:
            raise exc

    def data_received(self, data):
        self.read_queue.put_nowait(data)

    def close(self):
        """Closes the client's connection to the server."""

        if not self.closed:
            self.closed = True
            if not self.transport.is_closing():
                self.transport.write_eof()
                self.transport.close()

    def abort(self):
        """Aborts the client's connection to the server."""

        self.transport.abort()
        self.close()

    def to_real_packet_checker(self, checker):
        if isinstance(checker, type):
            # Packet class
            return lambda x: isinstance(x, checker)
        elif isinstance(checker, int):
            # Packet id
            return lambda x: (x.get_id(self.ctx) == checker)

        return checker

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

            if real_checker is not None:
                # deepcopy to avoid mutable wackiness
                tmp_old = copy.deepcopy(real_checker)
                tmp_add = copy.deepcopy(real_c)

                real_checker = lambda x: (tmp_old(x) or tmp_add(x))
            else:
                real_checker = real_c

        self.packet_listeners[func] = real_checker

    def unregister_packet_listener(self, func):
        """Unregisters a packet listener."""

        self.packet_listeners.pop(func)

    def external_packet_listener(self, *checkers):
        """
        Decorator for packet listeners

        checkers is the same as in
        register_packet_listener
        """

        def dec(func):
            self.register_packet_listener(func, *checkers)

            return func

        return dec

    async def read_packet(self):
        """
        Reads a packet from the server.

        Will return None if the connection
        gets closed, otherwise it will only
        return once it receives a packet.
        """

        while not self.closed:
            try:
                data = await asyncio.wait_for(self.read_queue.get(), 1)
                data = io.BytesIO(data)

                if self.comp_threshold > 0:
                    data_len = VarInt(data, ctx=self.ctx).value
                    if data_len > 0:
                        if data_len < self.comp_threshold:
                            self.close()
                            raise ValueError("Invalid data length for a compressed packet")

                        data = io.BytesIO(zlib.decompress(data.read(), bufsize=data_len))

                id = VarInt(data, ctx=self.ctx).value
                pack_class = self.packet_info.get(id)
                if pack_class is None:
                    pack_class = GenericPacket(id)

                return pack_class(data, ctx=self.ctx)
            except asyncio.TimeoutError:
                pass

        return None

    async def write_packet(self, pack, **kwargs):
        """
        Writes a packet to the server.

        pack can be either a Packet object,
        or it can be a Packet class, and then
        the sent packet will be made using that
        class and the keyword arguments.

        pack being a Packet class is preferred
        because then the context will be correctly
        passed to the sent packet.
        """

        if isinstance(pack, type):
            pack = pack(ctx=self.ctx, **kwargs)

        data = bytes(pack)

        if self.comp_threshold > 0:
            data_len = 0
            if len(data) >= self.comp_threshold:
                data_len = len(data)
                data = zlib.compress(data)

            data = bytes(VarInt(data_len, ctx=self.ctx)) + data

        data = bytes(VarInt(len(data), ctx=self.ctx)) + data

        if self.encryptor is not None:
            data = self.encryptor.update(data)

        self.transport.write(data)

    async def start(self):
        self.read_queue = asyncio.Queue()

        self.transport, _ = await asyncio.get_running_loop().create_connection(self.protocol_factory, self.address, self.port)

        await self.on_start()

    async def status(self):
        if self.current_state != enums.State.Handshaking:
            raise ValueError("Invalid state")

        await self.write_packet(serverbound.HandshakePacket,
            proto_version = self.ctx.proto,
            server_address = self.address,
            server_port = self.port,
            next_state = enums.State.Status,
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

    async def send_server_hash(self, server_hash):
        async with aiohttp.ClientSession() as s:
            async with s.post(f"{self.session_server}/join",
                data = json.dumps(
                    {
                        "accessToken": self.auth_token.access_token,
                        "selectedProfile": self.auth_token.profile.id,
                        "serverId": server_hash,
                    },
                    separators = (",", ":"),
                ),
                headers = {"content-type": "application/json"},
            ) as resp:
                if resp.status != 204:
                    raise ValueError(f"Invalid status code from session server: {resp.status}")

    async def login(self):
        if self.current_state != enums.State.Handshaking:
            raise ValueError("Invalid state")

        await self.auth_token.ensure()

        await self.write_packet(serverbound.HandshakePacket,
            proto_version = self.ctx.proto,
            server_address = self.address,
            server_port = self.port,
            next_state = enums.State.Login,
        )

        self.current_state = enums.State.Login

        await self.write_packet(serverbound.LoginStartPacket,
            name = self.auth_token.profile.name,
        )

    async def on_start(self):
        await self.login()

        while not self.closed:
            p = await self.read_packet()
            if p is None:
                continue

            tasks = []
            for func, checker in self.packet_listeners.items():
                if checker(p):
                    tasks.append(asyncio.create_task(func(p)))

            # Will this slow down the client too much maybe?
            await asyncio.gather(*tasks)

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
        server_hash = encryption.gen_server_hash(p.server_id, shared_secret, p.pub_key)

        await self.send_server_hash(server_hash)

        enc_secret, enc_token = encryption.encrypt_secret_and_token(p.pub_key, shared_secret, p.verify_token)

        await self.write_packet(serverbound.EncryptionResponsePacket,
            shared_secret = enc_secret,
            verify_token = enc_token,
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

    @packet_listener(clientbound.KeepAlivePacket)
    async def _on_keep_alive(self, p):
        await self.write_packet(serverbound.KeepAlivePacket,
            id = p.id,
        )
