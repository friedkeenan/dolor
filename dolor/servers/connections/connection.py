import asyncio
import uuid

from ... import enums
from ... import connection
from ...versions import Version
from ...packets import PacketContext, serverbound, clientbound

class ServerConnection(connection.Connection):
    def __init__(self, server, reader, writer):
        self.ctx = PacketContext(Version(None))

        super().__init__(serverbound)

        self.server = server

        self.reader = reader
        self.writer = writer

        self.should_listen_sequentially = True
        self.tasks = []

        self.central_task = None

        self.name = ""
        self.uuid = uuid.UUID(int=0)

    @property
    def is_player(self):
        return self.current_state == enums.State.Play

    async def disconnect(self, reason):
        if isinstance(reason, Exception):
            reason = f"{type(reason).__name__}: {reason}"

        packet = {
            enums.State.Login: clientbound.DisconnectLoginPacket,
            enums.State.Play:  clientbound.DisconnectPlayPacket,
        }.get(self.current_state)

        if packet is not None:
            try:
                await self.write_packet(packet,
                    reason = reason,
                )
            except:
                pass

        self.close()
        await self.wait_closed()

    async def set_compression(self, threshold):
        await self.write_packet(clientbound.SetCompressionPacket,
            threshold = threshold,
        )

        self.comp_threshold = threshold

    async def login_success(self):
        await self.write_packet(clientbound.LoginSuccessPacket,
            uuid     = self.uuid,
            username = self.name,
        )

        self.current_state              = enums.State.Play
        self.should_listen_sequentially = False

        self.central_task = asyncio.create_task(self.server.central_connection_task(self))

    async def message(self, message, *, position=enums.ChatPosition.Chat, sender=None):
        if sender is None:
            sender = uuid.UUID(int=0)
        else:
            sender = sender.uuid

        await self.write_packet(clientbound.ChatMessagePacket(
            data     = message,
            position = position,
            sender   = sender,
        ))

    def close(self):
        if not self.is_closing():
            super().close()

            if self.central_task is not None:
                self.central_task.cancel()

    async def wait_closed(self):
        if self.is_closing():
            await super().wait_closed()

            if self.central_task is not None:
                # Use asyncio.wait_for?
                await self.central_task

    def create_task(self, coro):
        """Internal function used to ensure that all listeners complete."""

        real_task = asyncio.create_task(coro)
        self.tasks.append(real_task)

        async def task():
            try:
                await real_task
            finally:
                self.tasks.remove(real_task)

        return asyncio.create_task(task())

    async def write_packet(self, *args, **kwargs):
        p = await super().write_packet(*args, **kwargs)

        await self.server.listen_to_packet(self, p, outgoing=True)

        return p

    def __eq__(self, other):
        return self.uuid == other.uuid

    def __hash__(self):
        return hash(self.uuid)

    def __repr__(self):
        return f"{type(self).__name__}({repr(self.name)}, {repr(self.uuid)})"
