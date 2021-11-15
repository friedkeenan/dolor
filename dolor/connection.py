"""Contains :class:`~.Connection`."""

import asyncio
import io
import zlib
import pak

from .versions import Version
from .packets import (
    PacketContext,
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

class Connection:
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
    ctx : :class:`~.PacketContext`
        The context for packets sent to and received by the :class:`Connection`.
    compression_threshold : :class:`int`
        The maximum size of a packet before it is compressed.

        If less than zero, then packet compression is disabled.
    reader : :class:`asyncio.StreamReader`
        The stream for incoming data.
    writer : :class:`asyncio.StreamWriter`
        The stream for outgoing data.
    """

    # TODO: Figure out a feasible way to test this.

    def __init__(self, bound, *, version):
        self._bound_packet_parent = {
            serverbound: ServerboundPacket,
            clientbound: ClientboundPacket,
        }[bound]

        self.ctx   = PacketContext(version)
        self.state = ConnectionState.Handshaking

        self.compression_threshold = -1

        self.reader = None
        self.writer = None

        self._read_lock      = asyncio.Lock()
        self._specific_reads = {}

    @property
    def version(self):
        """The :class:`~.Version` of the :class:`Connection`."""

        return self.ctx.version

    @version.setter
    def version(self, value):
        self.ctx = PacketContext(value)

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

    def is_closing(self):
        """Checks if the :class:`Connection` is closed or being closed.

        Returns
        -------
        :class:`bool`
            Whether the :class:`Connection` is closed or being closed.
        """

        return self.writer is not None and self.writer.is_closing()

    def close(self):
        """Closes the :class:`Connection`.

        Should be used alongside the :meth:`wait_closed` method.
        """

        # 'StreamReader's do not have a 'close' method.
        if self.writer is not None:
            self.writer.close()

    async def wait_closed(self):
        """Waits until the connection is closed."""

        if self.writer is not None:
            await self.writer.wait_closed()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, exc_traceback):
        self.close()
        await self.wait_closed()

    def create_packet(self, packet_cls, **kwargs):
        """Creates a packet using the :attr:`ctx` attribute.

        Parameters
        ----------
        packet_class : subclass of :class:`~.Packet`
            The :class:`~.Packet` to create.
        **kwargs
            The specified attributes of the :class:`~.Packet`
            and their corresponding values.

        Returns
        -------
        :class:`~.Packet`
            The created :class:`~.Packet`.
        """

        return packet_cls(ctx=self.ctx, **kwargs)

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

    async def _read_general_packet(self):
        data = b""

        try:
            # Make sure reading packets is atomic.
            async with self._read_lock:
                length_data = b""

                while True:
                    length_data += await self.reader.readexactly(1)

                    try:
                        length = types.VarInt.unpack(length_data, ctx=self.ctx)
                    except types.VarNumBufferLengthError as e:
                        raise e
                    except Exception:
                        # If we fail to read a VarInt, read the next byte and try again.
                        continue

                    break

                data = await self.reader.readexactly(length)

        except asyncio.IncompleteReadError:
            self.close()
            await self.wait_closed()

            return None

        data = await self._decompressed_file_object(data)

        id         = types.VarInt.unpack(data)
        packet_cls = self._packet_for_id(id, self._available_packets, ctx = self.ctx)

        if packet_cls is None:
            packet_cls = GenericPacketWithID(id)

        return packet_cls.unpack(data, ctx=self.ctx)

    def _dispatch_to_specific_reads(self, packet):
        # Make a copy of the items so we can modify the dictionary within the same loop.
        for packet_cls, packet_holder in list(self._specific_reads.items()):
            if isinstance(packet, packet_cls):
                packet_holder.set(packet)
                self._specific_reads.pop(packet_cls)

                # Don't break here since there could be other
                # reads that requested a more specific subclass
                # of 'packet_cls'.

    async def continuously_read_packets(self):
        """Continuously reads and yields all incoming :class:`Packets <.Packet>`.

        This must be iterated over for :meth:`read_packet` to function.

        This will continue to yield :class:`Packets <.Packet>` until the
        :class:`Connection` is closed.
        """

        while not self.is_closing():
            packet = await self._read_general_packet()

            if packet is None:
                return

            self._dispatch_to_specific_reads(packet)

            yield packet

    async def read_packet(self, packet_to_read):
        """Reads a specific type of :class:`.Packet` from the incoming packets.

        Requires :meth:`continuously_read_incoming_packets` to be iterated over.

        Parameters
        ----------
        packet_to_read : subclass of :class:`.Packet`
            The type of the :class:`.Packet` to read.

        Returns
        -------
        :class:`.Packet` or ``None``
            The specified incoming :class:`.Packet`.

            Returns ``None`` when the :class:`Connection` is closed.
        """

        packet_holder = self._specific_reads.get(packet_to_read)
        if packet_holder is None:
            packet_holder                        = util.AsyncValueHolder()
            self._specific_reads[packet_to_read] = packet_holder

        # TODO: Is there a cleaner way to wait for a packet?
        # Maybe with futures?
        while not self.is_closing():
            try:
                return await asyncio.wait_for(packet_holder.get(), 1)
            except asyncio.TimeoutError:
                pass

        return None

    def _compressed_data(self, data):
        if self.compression_enabled:
            data_len = 0

            if len(data) > self.compression_threshold:
                data_len = len(data)
                data     = zlib.compress(data)

            data = types.VarInt.pack(data_len, ctx=self.ctx) + data

        return data

    async def write_packet(self, packet_cls, **kwargs):
        """Writes an outgoing :class:`~.Packet`.

        This method creates a :class:`~.Packet` instance using the :meth:`create_packet`
        method. If you wish to write a pre-existing :class:`~.Packet` instance,
        then the :meth:`write_packet_instance` method should be used instea.

        This method ultimately calls :meth:`write_packet_instance`.

        Parameters
        ----------
        packet_cls : subclass of :class:`~.Packet`
            The type of :class:`~.Packet` to write.
        **kwargs
            The attributes and corresponding attributes of the written :class:`~.Packet`.

        Returns
        -------
        :class:`~.Packet`
            The written :class:`~.Packet`.
        """

        return await self.write_packet_instance(self.create_packet(packet_cls, **kwargs))

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

        Returns
        -------
        :class:`~.Packet`
            The written :class:`~.Packet`, i.e. ``packet``.
        """

        data = packet.pack(ctx=self.ctx)
        data = self._compressed_data(data)
        data = types.VarInt.pack(len(data), ctx=self.ctx) + data

        self.writer.write(data)
        await self.writer.drain()

        return packet
