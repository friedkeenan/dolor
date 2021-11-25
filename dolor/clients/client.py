"""Contains :class:`~.Client`."""

import asyncio
import time
from aioconsole import aprint

from ..connection import Connection
from ..packet_handler import packet_listener, PacketHandler
from ..packets import ConnectionState, clientbound, serverbound

from .. import types

__all__ = [
    "Client",
]

class Client(Connection, PacketHandler):
    """A Minecraft client.

    Parameters
    ----------
    address : :class:`str`
        The address of the :class:`~.Server` to connect to.
    port : :class:`int`
        The port of the :class:`~.Server` to connect to.
    version : versionlike
        The :class:`~.Version` for the :class:`Client`.
    name : :class:`str` or ``None``
        The name of the player.

        If ``None``, then the player's name is gotten from
        authentication if possible.

        Upon a successful login, this attribute is updated
        to the value of :attr:`clientbound.LoginSuccessPacket.username <.LoginSuccessPacket.username>`.
    translations : pathlike or string file object or :class:`dict` or ``None``
        If not ``None``, then passed to :meth:`types.Chat.Chat.load_translations <.Chat.Chat.load_translations>`.
    """

    def __init__(
        self,
        address,
        port = 25565,
        *,
        version,
        name         = None,
        translations = None,
    ):
        # Cannot use 'super' here because of multiple inheritance with non-matching constructors.
        Connection.__init__(self, clientbound, version=version)
        PacketHandler.__init__(self)

        self.address = address
        self.port    = port

        self.name = name

        if translations is not None:
            types.Chat.Chat.load_translations(translations)

        self._listen_sequentially = True

    def register_packet_listener(self, listener, *packet_checkers, outgoing=False):
        """Overrides :meth:`.PacketHandler.register_packet_listener`.

        This adds the ``outgoing`` keyword argument to
        check against for :class:`~.Packet` listeners.

        Parameters
        ----------
        listener : coroutine function
            The :class:`~.Packet` listener.
        *packet_checkers
            See :meth:`.PacketHandler.register_packet_listener`.
        outgoing : :class:`bool`
            Whether ``listener`` listens to outgoing :class:`Packets <.Packet>`,
            i.e. those that are sent to the :class:`~.Server`.
        """

        super().register_packet_listener(listener, *packet_checkers, outgoing=outgoing)

    async def _listen_to_packet(self, packet, **check_kwargs):
        async with self.listener_task_context(listen_sequentially=self._listen_sequentially):
            for listener in self.listeners_for_packet(self, packet, **check_kwargs):
                self.create_listener_task(listener(packet))

    async def _listen_to_incoming_packets(self):
        try:
            async for packet in self.continuously_read_packets():
                await self._listen_to_packet(packet, outgoing=False)
        finally:
            await self.end_listener_tasks()

    async def write_packet_instance(self, packet):
        """Overrides :meth:`.Connection.write_packet_instance`.

        This allows listening to outgoing :class:`Packets <.Packet>`.
        """

        await self._listen_to_packet(packet, outgoing=True)

        return await super().write_packet_instance(packet)

    async def startup(self):
        """Called when the :class:`Client` is started.

        Opens a connection, setting the :attr:`reader <.Connection.reader>` and
        :attr:`writer <.Connection.writer>` attributes.
        """

        self.reader, self.writer = await asyncio.open_connection(self.address, self.port)

    async def on_start(self):
        """Called after :meth:`startup`.

        By default calls :meth:`login`.
        """

        await self.login()

    async def start(self):
        """Starts the :class:`Client`.

        This should only be used if you're already in a coroutine.
        Otherwise, you should use the :meth:`run` method.

        This should not be overridden. Instead override the :meth:`startup`
        and/or :meth:`on_start` methods.
        """

        await self.startup()

        async with self:
            await self.on_start()

    def run(self):
        """Runs the :class:`Client`.

        Calls :meth:`start` with :func:`asyncio.run`.
        """

        asyncio.run(self.start())

    async def status(self):
        """Gets the status of the :class:`~.Server` the :class:`Client` was directed at.

        Returns
        -------
        :class:`clientbound.ResponsePacket.Response.Response <.ResponsePacket.Response.Response>`
            The response from the :class:`~.Server`.
        :class:`int`
            The ping to the :class:`~.Server`, in milliseconds.

        Raises
        ------
        :exc:`ValueError`
            If the :class:`Client` is not in the :attr:`.ConnectionState.Handshaking` state.
        :exc:`RuntimeError`
            If the :class:`Client` cannot get the status of the :class:`~.Server`.
        """

        if self.state != ConnectionState.Handshaking:
            raise ValueError(f"Invalid connection state for status: {self.state}")

        await self.write_packet(
            serverbound.HandshakePacket,

            protocol       = self.version.protocol,
            server_address = self.address,
            server_port    = self.port,
            next_state     = ConnectionState.Status,
        )

        self.state = ConnectionState.Status

        await self.write_packet(serverbound.RequestPacket)
        await self.write_packet(
            serverbound.PingPacket,

            payload = int(time.time() * 1000)
        )

        response = None
        ping     = None

        async for packet in self.continuously_read_packets():
            if isinstance(packet, clientbound.ResponsePacket):
                response = packet.response
            elif isinstance(packet, clientbound.PongPacket):
                ping = int(time.time() * 1000) - packet.payload

            if response is not None and ping is not None:
                break

        self.close()

        # If packet reading prematurely stops, raise an error.
        if response is None or ping is None:
            raise RuntimeError("Could not get the status of the server")

        return response, ping

    async def login(self):
        """Logs into the :class:`~.Server` and begins listening to incoming :class:`Packets <.Packet>`.

        If the :class:`Client` has not been given authentication data, then
        it may only connect to "offline" :class:`Servers <.Server>` and the
        ``name`` parameter must be passed on construction.

        Raises
        ------
        :exc:`ValueError`
            If the :class:`Client` is not in the :attr:`.ConnectionState.Handshaking` state.
        """

        if self.state != ConnectionState.Handshaking:
            raise ValueError(f"Invalid connection state for login: {self.state}")

        if self.name is None:
            # TODO: Authentication.
            raise NotImplementedError

        # We do not want to read packets before handling a
        # 'SetCompressionPacket' or 'EncryptionRequestPacket',
        # as that would end up with reading the packets incorrectly.
        self._listen_sequentially = True

        await self.write_packet(
            serverbound.HandshakePacket,

            protocol       = self.version.protocol,
            server_address = self.address,
            server_port    = self.port,
            next_state     = ConnectionState.Login,
        )

        self.state = ConnectionState.Login

        await self.write_packet(
            serverbound.LoginStartPacket,

            name = self.name,
        )

        await self._listen_to_incoming_packets()

    # Default packet listeners.

    @packet_listener(clientbound.DisconnectPacket)
    async def _on_disconnect(self, packet):
        # TODO: Use aiologger?
        await aprint("Disconnected:", packet.reason.flatten())

        self.close()
        await self.wait_closed()

    @packet_listener(clientbound.EncryptionRequestPacket)
    async def _on_encryption_request(self, packet):
        # TODO: Encryption.
        raise NotImplementedError

    @packet_listener(clientbound.SetCompressionPacket)
    async def _on_set_compression(self, packet):
        self.compression_threshold = packet.threshold

    @packet_listener(clientbound.LoginSuccessPacket)
    async def _on_login_success(self, packet):
        # Update our name to what the server tells us.
        self.name = packet.username

        self.state = ConnectionState.Play

        # Packets in the play state should be fine to
        # handle completely asynchronously.
        self._listen_sequentially = False

    @packet_listener(clientbound.KeepAlivePacket)
    async def _on_keep_alive(self, packet):
        await self.write_packet(
            serverbound.KeepAlivePacket,

            keep_alive_id = packet.keep_alive_id,
        )
