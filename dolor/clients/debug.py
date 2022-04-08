r"""Contains :class:`~.Client`\s that give debug information."""

import pak
from aioconsole import aprint

from ..packets import Packet, GenericPacket
from .client import Client

__all__ = [
    "LoggingClient",
]

class LoggingClient(Client):
    r"""A :class:`~.Client` which logs :class:`~.Packet`\s

    :meta no-undoc-members:

    Parameters
    ----------
    *args, **kwargs
        Forwarded to :class:`~.Client`.

    Attributes
    ----------
    log_outgoing_packets : :class:`bool`
        Whether :class:`~.Packet`\s written to the :class:`~.Server`
        should be logged.
    log_generic_packets : :class:`bool`
        Whether :class:`~.GenericPacket`\s should be logged.

        .. note::
            Setting this to ``True`` will log *many* packets,
            since any :class:`~.Packet` whose structure isn't
            known will be consumed as a :class:`~.GenericPacket`.

    Examples
    --------
    ::

        import dolor

        class MyClient(dolor.clients.LoggingClient):
            # In this example we want to log packets written to the server.
            log_outgoing_packets = True

            # In this example we also want to log generic packets.
            log_generic_packets = True
    """

    log_outgoing_packets = False
    log_generic_packets  = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.log_outgoing_packets:
            self.register_packet_listener(self._on_outgoing_packet, Packet, outgoing=True)

    @classmethod
    def _should_log_packet(cls, packet):
        return cls.log_generic_packets or not isinstance(packet, GenericPacket)

    @pak.packet_listener(Packet)
    async def _on_incoming_packet(self, packet):
        if self._should_log_packet(packet):
            await aprint("Incoming:", packet)

    async def _on_outgoing_packet(self, packet):
        if self._should_log_packet(packet):
            await aprint("Outgoing:", packet)
