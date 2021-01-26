"""Contains :class:`~.Connection`."""

import abc
import asyncio
import zlib
import io

from . import enums
from . import util
from . import encryption
from .types import VarInt

from .packets import (
    GenericPacket,
    ServerboundPacket,
    ClientboundPacket,
    HandshakingPacket,
    StatusPacket,
    LoginPacket,
    PlayPacket,

    serverbound,
    clientbound,
)

class Connection:
    """A connection between a client and a server.

    Parameters
    ----------
    bound
        Where read packets are bound. Either :mod:`~.serverbound` or :mod:`~.clientbound`.

    Attributes
    ----------
    bound
        Either :class:`~.ServerboundPacket` or :class:`~.ClientboundPacket`.
        Used by :meth:`gen_packet_info` to populate the :attr:`packet_info`
        attribute.
    packet_info : :class:`dict`
        A dictionary whose keys are packet id's and whose values
        are subclasses of :class:`~.Packet`. Populated by :meth:`gen_packet_info`
        and used by :meth:`read_packet` to determine which id corresponds to
        which subclass of :class:`~.Packet`.
    read_lock : :class:`asyncio.Lock`
        The lock to make sure packet reads don't overlap.
    specific_reads : :class:`dict`
        A dictionary whose keys are subclasses of :class:`~.Packet`
        and whose values are :class:`~.AsyncValueHolder`.

        Used in :meth:`dispatch_packet` to send packets to specific reads
        that were made with :meth:`read_packet`.
    reader : :class:`asyncio.StreamReader`
        The reader for receiving packet data.
    writer : :class:`asyncio.StreamWriter`
        The writer for writing packet data.
    comp_threshold : :class:`int`
        The maximum size of a packet before it's compressed.

        If less than or equal to 0, then compression is disabled.
    """

    def __init__(self, bound):
        self.bound = {
            serverbound: ServerboundPacket,
            clientbound: ClientboundPacket,
        }[bound]

        self.current_state = enums.State.Handshaking

        self.read_lock      = asyncio.Lock()
        self.specific_reads = {}

        self.reader = None
        self.writer = None

        self.comp_threshold = 0

    def gen_packet_info(self, state, *, ctx=None):
        """Generates the :attr:`packet_info`.

        Parameters
        ----------
        state : :class:`~.State`
            Which state the packet info is for.
        ctx : :class:`~.PacketContext`, optional
            Which context the packet info is for.

        Returns
        -------
        :class:`dict`
            The packet info. See :attr:`packet_info` for a more thorough description.
        """

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
        """The connection's :class:`~.PacketContext`."""

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
        """The current :class:`~.State` of the connection."""

        return self._current_state

    @current_state.setter
    def current_state(self, value):
        self._current_state = value

        try:
            self.packet_info = self.gen_packet_info(value, ctx=self.ctx)
        except AttributeError:
            pass

    def is_closing(self):
        """Checks if the connection is closed or being closed.

        Returns
        -------
        :class:`bool`
            Whether the connection is closed or being closed.
        """

        return self.writer is not None and self.writer.is_closing()

    def close(self):
        """Closes the connection.

        Should be used alongside the :meth:`wait_closed` method.
        """

        if self.writer is not None:
            self.writer.close()

    async def wait_closed(self):
        """Waits until the connection is closed."""

        if self.writer is not None:
            await self.writer.wait_closed()

    def __del__(self):
        self.close()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, exc_tb):
        self.close()
        await self.wait_closed()

    def enable_encryption(self, shared_secret):
        """Enables encryption for the connection.

        Parameters
        ----------
        shared_secret
            The shared secret, either gotten from :func:`~.gen_shared_secret`
            or decrypted from :class:`~.EncryptionResponsePacket`.
        """

        cipher = encryption.gen_cipher(shared_secret)

        self.reader = encryption.EncryptedStream(self.reader, cipher.decryptor(), None)
        self.writer = encryption.EncryptedStream(self.writer, None, cipher.encryptor())

    def create_packet(self, pack_class, **kwargs):
        """Creates a packet with the connection's :attr:`ctx` attribute.

        Parameters
        ----------
        pack_class : subclass of :class:`~.Packet`
            The packet to create.
        kwargs
            The attributes of the packet to set.

        Returns
        -------
        :class:`~.Packet`
            The created packet.
        """

        return pack_class(ctx=self.ctx, **kwargs)

    def dispatch_packet(self, packet):
        """Dispatches a packet to calls of :meth:`read_packet` which specified `read_class`.

        Parameters
        ----------
        packet : :class:`~.Packet`
            The packet to dispatch.
        """

        to_remove = []

        for pack_class, holder in self.specific_reads.items():
            if isinstance(packet, pack_class):
                holder.set(packet)
                to_remove.append(pack_class)

        for pack_class in to_remove:
            self.specific_reads.pop(pack_class)

    async def read_packet(self, read_class=None):
        """Reads a packet.

        Parameters
        ----------
        read_class : subclass of :class:`~.Packet`, optional
            The packet you want to read. If unspecified, whatever
            the next packet is will be returned. Requires this method
            to be called elsewhere with ``read_class`` unspecified to work.

        Returns
        -------
        :class:`~.Packet` or ``None``
            If EOF is reached when reading the packet, then the connection
            will be closed and ``None`` will be returned. Otherwise the read
            packet will be returned.

        Raises
        ------
        :exc:`ValueError`
            If compression is enabled and the data length of the packet
            is greater than 0 but less than or equal to the
            :attr:`comp_threshold` attribute.
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
                if data_len <= self.comp_threshold:
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
        """Writes a packet.

        Parameters
        ----------
        packet : subclass of :class:`~.Packet` or :class:`~.Packet`
            If a subclass of :class:`~.Packet`, then the packet to write
            will be created by forwarding ``packet`` and ``kwargs`` to the
            :meth:`create_packet` method. Otherwise, ``packet`` is the
            packet to write.

            ``packet`` being a subclass of :class:`~.Packet` is preferred
            so that the packet is created with the correct context for
            the connection.
        kwargs
            The packet attributes to set. Only able to be passed if
            ``packet`` is a subclass of :class:`~.Packet`.

        Returns
        -------
        subclass of :class:`~.Packet`
            The written packet.

        Raises
        ------
        :exc:`TypeError`
            If ``kwargs`` is passed but ``packet`` isn't a subclass of
            :class:`~.Packet`.
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
        await self.writer.drain()

        return packet
