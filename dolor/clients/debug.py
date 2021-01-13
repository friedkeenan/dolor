from aioconsole import aprint

from ..packet_handler import packet_listener
from ..packets import Packet, GenericPacket
from .client import Client

class DebugClient(Client):
    print_outgoing_packets = False
    print_generic_packets  = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.print_outgoing_packets:
            self.register_packet_listener(self._on_outgoing_packet, Packet, outgoing=True)

    def _should_print_packet(self, p):
        return not (isinstance(p, GenericPacket) and not self.print_generic_packets)

    @packet_listener(Packet)
    async def _on_incoming_packet(self, p):
        if self._should_print_packet(p):
            await aprint("Incoming:", p)

    async def _on_outgoing_packet(self, p):
        if self._should_print_packet(p):
            await aprint("Outgoing:", p)
