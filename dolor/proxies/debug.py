from aioconsole import aprint

from ..packet_handler import packet_listener
from ..packets import Packet, GenericPacket, serverbound, clientbound
from .proxy import Proxy

class DebugProxy(Proxy):
    print_outgoing_packets = False
    print_generic_packets  = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.print_outgoing_packets:
            self.register_packet_listener(self._on_outgoing_serverbound_packet, Packet, bound=serverbound)
            self.register_packet_listener(self._on_outgoing_clientbound_packet, Packet, bound=clientbound)

    def _should_print_packet(self, p):
        return not (isinstance(p, GenericPacket) and not self.print_generic_packets)

    @packet_listener(Packet, bound=serverbound)
    async def _on_incoming_serverbound_packet(self, c, s, p):
        if self._should_print_packet(p):
            await aprint("Incoming:", p)

    @packet_listener(Packet, bound=clientbound)
    async def _on_incoming_clientbound_packet(self, c, s, p):
        if self._should_print_packet(p):
            await aprint("Incoming:", p)

    async def _on_outgoing_serverbound_packet(self, c, s, p):
        if self._should_print_packet(p):
            await aprint("Outgoing:", p)

    async def _on_outgoing_clientbound_packet(self, c, s, p):
        if self._should_print_packet(p):
            await aprint("Outgoing:", p)
