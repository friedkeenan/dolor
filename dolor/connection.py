"""Contains :class:`~.Connection`."""

import asyncio
import io
import zlib
import pak

from .versions import Version
from .packets import (
    Packet,
    ServerboundPacket,
    ClientboundPacket,
    ConnectionState,
    GenericPacketWithID,
    serverbound,
    clientbound,
)

from . import types
from . import util

__all__ = [
    "Connection",
]

class Connection(pak.io.Connection):
    """A connection between a :class:`~.Client` and :class:`~.Server`.

    Parameters
    ----------
    bound
        Either :mod:`~.serverbound` or :mod:`~.clientbound`, corresponding
        to where incoming packets are bound to.
    version : versionlike
        The :class:`~.Version` of the :class:`Connection`.

    Attributes
    ----------
    compression_threshold : :class:`int`
        The maximum size of a packet before it is compressed.

        If less than zero, then packet compression is disabled.
    """

    def __init__(self, bound, *, version):
        super().__init__(ctx=Packet.Context(version))

        self._bound_packet_parent = {
            serverbound: ServerboundPacket,
            clientbound: ClientboundPacket,
        }[bound]

        self.state = ConnectionState.Handshaking

        self.disable_compression()

    @property
    def version(self):
        """The :class:`~.Version` of the :class:`Connection`."""

        return self.ctx.version

    @version.setter
    def version(self, value):
        self.ctx = Packet.Context(value)

    @property
    def state(self):
        """The :class:`~.ConnectionState` of the :class:`Connection`."""

        return self._state

    @state.setter
    def state(self, value):
        self._available_packets = value.packet_base_class.subclasses() & self._bound_packet_parent.subclasses()

        self._state = value

    @property
    def compression_enabled(self):
        """Whether :class:`~.Packet` compression is enabled."""

        return self.compression_threshold >= 0

    def disable_compression(self):
        """Disables :class:`~.Packet` compression."""

        self.compression_threshold = -1

    @staticmethod
    @pak.util.cache
    def _packet_for_id(id, available_packets, *, ctx=None):
        for packet_cls in available_packets:
            packet_id = packet_cls.id(ctx=ctx)

            if packet_id is not None and packet_id == id:
                return packet_cls

        return None

    async def _decompressed_file_object(self, data):
        data = pak.util.file_object(data)

        if not self.compression_enabled:
            return data

        data_len = types.VarInt.unpack(data, ctx=self.ctx)

        if data_len > 0:
            if data_len <= self.compression_threshold:
                self.close()
                await self.wait_closed()

                raise ValueError(f"Invalid data length {data_len} for compression threshold {self.compression_threshold}")

            data = io.BytesIO(zlib.decompress(data.read(), bufsize=data_len))

        return data

    async def _read_next_packet(self):
        # We don't need to make sure reading is atomic since this method
        # is only called by 'continuously_read_packets' which does not
        # read several packets at once.

        length_data = b""

        while True:
            next_byte = await self.read_data(1)
            if next_byte is None:
                return None

            length_data += next_byte

            try:
                length = types.VarInt.unpack(length_data, ctx=self.ctx)

            except types.VarNumBufferLengthError:
                # Make sure we don't read the length forever.
                raise

            except asyncio.CancelledError:
                # Make sure we can be cancelled.
                raise

            except Exception:
                # If we fail to read a VarInt, read the next byte and try again.
                continue

            break

        data = await self.read_data(length)
        if data is None:
            return None

        data = await self._decompressed_file_object(data)

        packet_header = Packet.Header.unpack(data, ctx=self.ctx)
        packet_cls    = self._packet_for_id(packet_header.id, self._available_packets, ctx=self.ctx)

        if packet_cls is None:
            packet_cls = GenericPacketWithID(packet_header.id)

        return packet_cls.unpack(data, ctx=self.ctx)

    def _compressed_data(self, data):
        if self.compression_enabled:
            written_data_len = 0
            real_data_len    = len(data)

            if real_data_len > self.compression_threshold:
                written_data_len = real_data_len
                data             = zlib.compress(data)

            data = types.VarInt.pack(written_data_len, ctx=self.ctx) + data

        return data

    async def write_packet_instance(self, packet):
        """Writes an outgoing :class:`~.Packet` instance.

        Warnings
        --------
        In most cases, the :meth:`write_packet` method should be used instead.
        This method should only be used if you have a pre-existing :class:`~.Packet`
        instance.

        Parameters
        ----------
        packet : :class:`~.Packet`
            The :class:`~.Packet` to write.
        """

        data = packet.pack(ctx=self.ctx)
        data = self._compressed_data(data)
        data = types.VarInt.pack(len(data), ctx=self.ctx) + data

        await self.write_data(data)
