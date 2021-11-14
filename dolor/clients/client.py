"""Contains :class:`~.Client`."""

import asyncio
import time

from ..connection import Connection
from ..packets import ConnectionState, clientbound, serverbound

from .. import types

__all__ = [
    "Client",
]

class Client(Connection):
    """A Minecraft client.

    Parameters
    ----------
    address : :class:`str`
        The address of the :class:`~.Server` to connect to.
    port : :class:`int`
        The port of the :class:`~.Server` to connect to.
    version : versionlike
        The :class:`~.Version` for the :class:`Client`.
    translations : pathlike or string file object or :class:`dict` or ``None``
        If not ``None``, then passed to :meth:`types.Chat.Chat.load_translations <.Chat.Chat.load_translations>`.
    """

    def __init__(
        self,
        address,
        port = 25565,
        *,
        version,
        translations = None,
    ):
        super().__init__(clientbound, version=version)

        self.address = address
        self.port    = port

        if translations is not None:
            types.Chat.Chat.load_translations(translations)

    async def startup(self):
        """Called when the :class:`Client` is started.

        By default initializes the :attr:`reader <.Connection.reader>` and
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

        async for packet in self.continuously_read_incoming_packets():
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
        raise NotImplementedError
