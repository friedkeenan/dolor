import abc
import asyncio
import zlib
import io

from . import enums
from . import util
from . import encryption
from .types import VarInt
from .packets import GenericPacket, HandshakingPacket, StatusPacket, LoginPacket, PlayPacket

class Connection:
    def __init__(self, bound):
        self.bound = bound
        self.current_state = enums.State.Handshaking

        self.read_lock      = asyncio.Lock()
        self.specific_reads = {}

        self.reader = None
        self.writer = None

        self.comp_threshold = 0

    def gen_packet_info(self, state, *, ctx=None):
        state_class = {
            enums.State.Handshaking: HandshakingPacket,
            enums.State.Status:      StatusPacket,
            enums.State.Login:       LoginPacket,
            enums.State.Play:        PlayPacket,
        }[state]

        ret = {}

        for c in util.get_subclasses(state_class) & util.get_subclasses(self.bound):
            id = c.get_id(ctx=ctx)

            if id is not None:
                ret[id] = c

        return ret

    @property
    def ctx(self):
        return self._ctx

    @ctx.setter
    def ctx(self, value):
        self._ctx = value

        try:
            self.packet_info = self.gen_packet_info(self.current_state, ctx=value)
        except AttributeError:
            pass

    @property
    def current_state(self):
        return self._current_state

    @current_state.setter
    def current_state(self, value):
        self._current_state = value

        try:
            self.packet_info = self.gen_packet_info(value, ctx=self.ctx)
        except AttributeError:
            pass

    def is_closing(self):
        return self.writer is not None and self.writer.is_closing()

    def close(self):
        if self.writer is not None:
            self.writer.close()

    async def wait_closed(self):
        await self.writer.wait_closed()

    def __del__(self):
        self.close()

    def create_packet(self, pack_class, **kwargs):
        """
        Utility method for creating a packet
        with the correct context.
        """

        return pack_class(ctx=self.ctx, **kwargs)

    def dispatch_packet(self, packet):
        to_remove = []

        for pack_class, holder in self.specific_reads.items():
            if isinstance(packet, pack_class):
                holder.set(packet)
                to_remove.append(pack_class)

        for pack_class in to_remove:
            self.specific_reads.pop(pack_class)

    async def read_packet(self, read_class=None):
        """
        Reads a packet.

        If read_class is not None, then
        it will return the next packet
        of that class. Requires this
        function to be called with no
        arguments elsewhere to work.

        Will return None and close the
        connection if eof is reached.
        """

        if read_class is not None:
            packet_holder = self.specific_reads.get(read_class)

            if packet_holder is None:
                packet_holder                   = util.AsyncValueHolder()
                self.specific_reads[read_class] = packet_holder

            while not self.is_closing():
                try:
                    return await asyncio.wait_for(packet_holder.get(), 1)
                except asyncio.TimeoutError:
                    pass

            return None

        data = b""

        try:
            async with self.read_lock:
                length_buf = b""
                length     = -1

                while True:
                    length_buf += await self.reader.readexactly(1)

                    try:
                        length = VarInt.unpack(length_buf, ctx=self.ctx)
                    except:
                        continue

                    break

                if length >= 0:
                    data = await self.reader.readexactly(length)

        except asyncio.IncompleteReadError:
            self.close()

            return None

        data = io.BytesIO(data)

        if self.comp_threshold > 0:
            data_len = VarInt.unpack(data, ctx=self.ctx)

            if data_len > 0:
                if data_len < self.comp_threshold:
                    self.close()
                    await self.wait_closed()

                    raise ValueError(f"Invalid data length ({data_len}) for compression threshold ({self.comp_threshold})")

                data = io.BytesIO(zlib.decompress(data.read(), bufsize=data_len))

        id         = VarInt.unpack(data, ctx=self.ctx)
        pack_class = self.packet_info.get(id)

        if pack_class is None:
            pack_class = GenericPacket(id)

        packet = pack_class.unpack(data, ctx=self.ctx)

        self.dispatch_packet(packet)

        return packet

    async def write_packet(self, packet, **kwargs):
        """
        Writes a packet.

        Returns the written packet.

        packet can be either a Packet object,
        or it can be a Packet class, and then
        the sent packet will be made using that
        class and the keyword arguments.

        packet being a Packet class is preferred
        because then the context will be correctly
        passed to the sent packet.
        """

        if isinstance(packet, type):
            packet = self.create_packet(packet, **kwargs)
        elif len(kwargs) > 0:
            raise TypeError("Packet object passed with keyword arguments")

        data = packet.pack(ctx=self.ctx)

        if self.comp_threshold > 0:
            data_len = 0

            if len(data) > self.comp_threshold:
                data_len = len(data)
                data     = zlib.compress(data)

            data = VarInt.pack(data_len, ctx=self.ctx) + data

        data = VarInt.pack(len(data), ctx=self.ctx) + data

        self.writer.write(data)

        return packet

    async def drain(self):
        await self.writer.drain()
