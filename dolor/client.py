import asyncio
import io

from . import enums
from . import util
from .types import *
from .packets import *

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

            # TODO: Clean this up
            if len(self.buffer) == self.length:
                self.client.data_received(self.buffer[:self.length])

                del self.buffer[:self.length]
                self.length = 0
            else:
                while len(self.buffer) > self.length:
                    # TODO: Act accordingly if we don't get enough data for a VarInt
                    if self.length == 0:
                        self.length = VarInt(self.buffer)
                        del self.buffer[:len(self.length)]
                        self.length = self.length.value

                    if len(self.buffer) >= self.length:
                        self.client.data_received(self.buffer[:self.length])

                        del self.buffer[:self.length]
                        self.length = 0

    def __init__(self, address, port=25565):
        self.address = address
        self.port = port

        self.ctx = PacketContext()
        self.current_state = enums.State.Handshaking

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
        pass

    def connection_lost(self, exc):
        pass

    def data_received(self, data):
        data = io.BytesIO(data)
        
        id = VarInt(data).value
        pack_class = self.packet_info[id]

        self.read_queue.put_nowait(pack_class(data, ctx=self.ctx))

    async def read_packet(self):
        return await self.read_queue.get()

    async def write_packet(self, pack):
        self.transport.write(bytes(pack))

    async def connect(self):
        self.read_queue = asyncio.Queue()
        self.transport, self.protocol = await asyncio.get_running_loop().create_connection(self.protocol_factory, self.address, self.port)

        await self.status()

    async def status(self):
        if self.current_state != enums.State.Handshaking:
            raise ValueError("Invalid state")

        await self.write_packet(serverbound.HandshakePacket(
            proto_version = -1,
            server_address = self.address,
            server_port = self.port,
            next_state = enums.State.Status,
        ))

        self.current_state = enums.State.Status

        await self.write_packet(serverbound.RequestPacket())
        resp = await self.read_packet()

        print("Response:", resp)

        await self.write_packet(serverbound.PingPacket(payload=0))
        pong = await self.read_packet()
        print("Pong:", pong)

    def run(self):
        asyncio.run(self.connect())