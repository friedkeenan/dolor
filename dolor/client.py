import asyncio
import aiohttp
import io
import zlib
import time

from . import enums
from . import util
from . import versions
from . import encryption
from .types import *
from .packets import *
from .yggdrasil import AuthenticationToken

class Client:
    class Protocol(asyncio.Protocol):
        def __init__(self, client):
            self.client = client

            self.buffer = bytearray()
            self.length = 0

            self.length_buf = b""

        def connection_made(self, transport):
            self.client.connection_made()

        def connection_lost(self, exc):
            self.client.connection_lost(exc)

        def data_received(self, data):
            self.buffer.extend(data)

            while len(self.buffer) != 0 and len(self.buffer) >= self.length:
                buf = io.BytesIO(self.buffer)

                # Perform decryption in the protocol because
                # the length is also encrypted
                if self.client.decryptor is not None:
                    buf = encryption.EncryptedFileObject(buf, self.client.decryptor, self.client.encryptor)

                if self.length <= 0:
                    # Sorta manually read length because we're not
                    # guaranteed to have a full VarInt
                    while True:
                        tmp = buf.read(1)
                        if len(tmp) < 1:
                            return

                        del self.buffer[:1]
                        self.length_buf += tmp

                        if tmp[0] & 0x80 == 0:
                            self.length = VarInt(self.length_buf).value
                            self.length_buf = b""

                            break

                        if len(self.length_buf) >= 5:
                            raise ValueError("VarInt is too big")

                if len(self.buffer) >= self.length:
                    self.client.data_received(buf.read(self.length))

                    del self.buffer[:self.length]
                    self.length = 0

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
    ):
        if isinstance(version, int):
            proto = version
        else:
            proto = versions.versions[version]

        self.ctx = PacketContext(proto)

        self.address = address
        self.port = port

        self.auth_token = AuthenticationToken(
            access_token = access_token,
            client_token = client_token,
            username = username,
            password = password,
        )

        self.current_state = enums.State.Handshaking

        self.closed = True

        self.transport = None
        self.read_queue = None
        self.decryptor = None
        self.encryptor = None

        self.comp_threshold = 0

        self.packet_listeners = {}

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
        return self.Protocol(self)

    def connection_made(self):
        self.closed = False

    def connection_lost(self, exc):
        self.closed = True

    def data_received(self, data):
        data = io.BytesIO(data)

        if self.comp_threshold > 0:
            data_len = VarInt(data).value
            if data_len > 0:
                if data_len < self.comp_threshold:
                    self.close()
                    raise ValueError("Invalid data length for a compressed packet")

                data = io.BytesIO(zlib.decompress(data.read(), bufsize=data_len))

        id = VarInt(data).value
        pack_class = self.packet_info.get(id)
        if pack_class is None:
            pack_class = GenericPacket(id)

        self.read_queue.put_nowait(pack_class(data, ctx=self.ctx))

    def close(self):
        self.closed = True
        if not self.transport.is_closing():
            self.transport.write_eof()
            self.transport.close()

    def abort(self):
        self.transport.abort()
        self.close()

    def register_packet_listener(self, func, checker):
        """
        Registers a packet listener.

        func is an async function and checker
        is either a packet class, a packet id,
        or a function that returns whether the
        listener should be called.
        """

        real_checker = checker
        if isinstance(checker, type):
            # Packet class
            real_checker = lambda x: isinstance(x, checker)
        elif isinstance(checker, int):
            # Packet id
            real_checker = lambda x: (x.get_id(self.ctx) == checker)

        self.packet_listeners[func] = real_checker

    def packet_listener(self, checker):
        """
        Decorator for packet listeners

        checker is the same as in
        register_packet_listener
        """

        def dec(func):
            self.register_packet_listener(func, checker)

            return func

        return dec

    async def read_packet(self):
        return await self.read_queue.get()

    async def write_packet(self, pack):
        data = bytes(pack)

        if self.comp_threshold > 0:
            data_len = 0
            if len(data) >= self.comp_threshold:
                data_len = len(data)
                data = zlib.compress(data)

            data = bytes(VarInt(data_len)) + data

        data = bytes(VarInt(len(data))) + data

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

        await self.write_packet(serverbound.HandshakePacket(
            proto_version = self.ctx.proto,
            server_address = self.address,
            server_port = self.port,
            next_state = enums.State.Status,
        ))

        self.current_state = enums.State.Status

        await self.write_packet(serverbound.RequestPacket())
        resp = await self.read_packet()

        await self.write_packet(serverbound.PingPacket(payload=int(time.time() * 1000)))
        pong = await self.read_packet()

        self.close()

        return resp.response, int(time.time() * 1000) - pong.payload

    async def send_server_hash(self, server_hash):
        async with aiohttp.ClientSession() as s:
            async with s.post("https://sessionserver.mojang.com/session/minecraft/join",
                data = json.dumps(
                    {
                        "accessToken": self.auth_token.access_token,
                        "selectedProfile": self.auth_token.profile.id,
                        "serverId": server_hash
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

        await self.write_packet(serverbound.HandshakePacket(
            proto_version = self.ctx.proto,
            server_address = self.address,
            server_port = self.port,
            next_state = enums.State.Login,
        ))

        self.current_state = enums.State.Login

        await self.write_packet(serverbound.LoginStartPacket(
            name = self.auth_token.profile.name,
        ))

        enc_req = await self.read_packet()
        if not isinstance(enc_req, clientbound.EncryptionRequestPacket):
            raise ValueError("Invalid packet. Offline server?")

        shared_secret = encryption.gen_shared_secret()
        server_hash = encryption.gen_server_hash(enc_req.server_id, shared_secret, enc_req.pub_key)

        await self.send_server_hash(server_hash)

        enc_secret, enc_token = encryption.encrypt_secret_and_token(enc_req.pub_key, shared_secret, enc_req.verify_token)

        await self.write_packet(serverbound.EncryptionResponsePacket(
            shared_secret = enc_secret,
            verify_token = enc_token,
        ))

        cipher = encryption.gen_cipher(shared_secret)
        self.decryptor = cipher.decryptor()
        self.encryptor = cipher.encryptor()

        p = await self.read_packet()

        if isinstance(p, clientbound.SetCompressionPacket):
            self.comp_threshold = p.threshold

            p = await self.read_packet()
            if not isinstance(p, clientbound.LoginSuccessPacket):
                raise ValueError("Invalid packet")
        elif not isinstance(p, clientbound.LoginSuccessPacket):
            raise ValueError("Invalid packet")

        self.current_state = enums.State.Play

    async def on_start(self):
        await self.login()

        while True:
            p = await self.read_packet()

            for func, checker in self.packet_listeners.items():
                if checker(p):
                    asyncio.create_task(func(p))

    def run(self):
        asyncio.run(self.start())