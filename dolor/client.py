import asyncio
import io
import time

from . import enums
from . import util
from . import versions
from .types import *
from .packets import *
from .yggdrasil import AuthenticationToken

class Client:
    class Protocol(asyncio.Protocol):
        def __init__(self, client):
            self.client = client

            self.buffer = bytearray()
            self.length = 0

        def connection_made(self, transport):
            self.client.connection_made()

        def connection_lost(self, exc):
            self.client.connection_lost(exc)

        def data_received(self, data):
            self.buffer.extend(data)

            while len(self.buffer) != 0 and len(self.buffer) >= self.length:
                if self.length <= 0:
                    try:
                        self.length = VarInt(self.buffer)
                    except:
                        return

                    del self.buffer[:len(self.length)]
                    self.length = self.length.value

                if len(self.buffer) >= self.length:
                    self.client.data_received(self.buffer[:self.length])

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
        self.transport = None

        self.auth_token = AuthenticationToken(
            access_token = access_token,
            client_token = client_token,
            username = username,
            password = password,
        )

        self.current_state = enums.State.Handshaking

        self.closed = True

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

        id = VarInt(data).value
        pack_class = self.packet_info[id]

        self.read_queue.put_nowait(pack_class(data, ctx=self.ctx))

    def close(self):
        self.closed = True
        if not self.transport.is_closing():
            self.transport.write_eof()
            self.transport.close()

    def abort(self):
        self.transport.abort()
        self.close()

    async def read_packet(self):
        return await self.read_queue.get()

    async def write_packet(self, pack):
        self.transport.write(bytes(pack))

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

    async def on_start(self):
        pass

    def run(self):
        asyncio.run(self.start())