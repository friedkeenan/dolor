import abc
import asyncio
import zlib
import io

from . import enums
from . import util
from . import encryption
from .types import VarInt
from .packets import GenericPacket, HandshakingPacket, StatusPacket, LoginPacket, PlayPacket

def packet_listener(*checkers):
    """Decorator for packet listeners within a class."""

    def dec(func):
        # Set the _checkers attribute to be later
        # recognized and registered by the class
        func._checkers = checkers

        return func

    return dec

class Connection(abc.ABC):
    class Protocol(asyncio.Protocol):
        def __init__(self, receiver):
            self.receiver = receiver

            self.buffer = bytearray()
            self.length = -1

        @property
        def ctx(self):
            try:
                return self.receiver.ctx
            except AttributeError:
                return None

        def connection_made(self, transport):
            self.receiver.connection_made(transport)

        def connection_lost(self, exc):
            self.receiver.connection_lost(exc)

        def data_received(self, data):
            self.buffer.extend(data)

            while len(self.buffer) >= self.length:
                buf = io.BytesIO(self.buffer)

                # Perform decryption in the protocol because
                # the length is also encrypted
                if self.receiver.decryptor is not None:
                    buf = encryption.EncryptedFileObject(buf, self.receiver.decryptor, self.receiver.encryptor)

                if self.length < 0:
                    try:
                        self.length = VarInt.unpack(buf, ctx=self.ctx)
                    except:
                        return

                    del self.buffer[:buf.tell()]

                if len(self.buffer) >= self.length:
                    self.receiver.data_received(buf.read(self.length))

                    del self.buffer[:self.length]
                    self.length = -1

    def __init__(self, bound):
        self.bound = bound

        self.current_state = enums.State.Handshaking

        self.closed     = True
        self.transport  = None
        self.read_queue = None
        self.decryptor  = None
        self.encryptor  = None

        self.comp_threshold = 0

        self.should_listen_sequentially = False

        self.packet_listeners = {}
        self.register_intrinsic_listeners()

    @property
    @abc.abstractmethod
    def intrinsic_functions(self):
        raise NotImplementedError

    def register_intrinsic_listeners(self):
        for func in self.intrinsic_functions:
            # If the function was decorated with
            # the packet_listener function, then
            # it will have the _checkers attribute
            if hasattr(func, "_checkers"):
                self.register_packet_listener(func, *func._checkers)

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

    def protocol_factory(self):
        return self.Protocol(self)

    def connection_made(self, transport):
        self.closed = False

    def connection_lost(self, exc):
        self.close()

        if exc is not None:
            raise exc

    def data_received(self, data):
        self.read_queue.put_nowait(data)

    def close(self):
        if not self.closed:
            self.closed = True

            if not self.transport.is_closing():
                self.transport.write_eof()
                self.transport.close()

    def abort(self):
        self.transport.abort()
        self.close()

    def to_real_packet_checker(self, checker):
        if isinstance(checker, type):
            # Packet class
            return lambda x: isinstance(x, checker)
        elif isinstance(checker, int):
            # Packet id
            return lambda x: (x.get_id(ctx=self.ctx) == checker)

        return checker

    def join_checkers(self, first, second):
        return lambda x: (first(x) or second(x))

    def register_packet_listener(self, func, *checkers):
        """
        Registers a packet listener.

        func is a coroutine function and each
        checker is either a packet class, a packet
        id, or a function that returns whether
        the listener should be called.
        """

        if not asyncio.iscoroutinefunction(func):
            raise TypeError(f"Packet listener {func.__name__} isn't a coroutine function")

        real_checker = None
        for c in checkers:
            real_c = self.to_real_packet_checker(c)

            if real_checker is None:
                real_checker = real_c
            else:
                real_checker = self.join_checkers(real_checker, real_c)

        self.packet_listeners[func] = real_checker

    def unregister_packet_listener(self, func):
        """Unregisters a packet listener."""

        self.packet_listeners.pop(func)

    def external_packet_listener(self, *checkers):
        """Decorator for external packet listeners."""

        def dec(func):
            self.register_packet_listener(func, *checkers)

            return func

        return dec

    def create_packet(self, pack_class, **kwargs):
        """
        Utility method for creating a packet
        with the correct context.
        """

        return pack_class(ctx=self.ctx, **kwargs)

    async def read_packet(self, *, timeout=None):
        """
        Reads a packet.

        If timeout is None, it will return
        None if the connection gets closed,
        otherwise it will only return once
        it receives a packet.

        Otherwise, it will try to return
        the packet before it times out no
        matter what.
        """

        while not self.closed:
            if timeout is not None:
                data = await asynio.wait_for(self.read_queue.get(), timeout)
            else:
                try:
                    data = await asyncio.wait_for(self.read_queue.get(), 1)
                except asyncio.TimeoutError:
                    continue

            data = io.BytesIO(data)

            if self.comp_threshold > 0:
                data_len = VarInt.unpack(data, ctx=self.ctx)

                if data_len > 0:
                    if data_len < self.comp_threshold:
                        self.close()

                        raise ValueError(f"Invalid data length ({data_len}) for compression threshold ({self.comp_threshold})")

                    data = io.BytesIO(zlib.decompress(data.read(), bufsize=data_len))

            id         = VarInt.unpack(data, ctx=self.ctx)
            pack_class = self.packet_info.get(id)

            if pack_class is None:
                pack_class = GenericPacket(id)

            return pack_class.unpack(data, ctx=self.ctx)

        return None

    async def write_packet(self, packet, **kwargs):
        """
        Writes a packet.

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

        data = packet.pack(ctx=self.ctx)

        if self.comp_threshold > 0:
            data_len = 0

            if len(data) > self.comp_threshold:
                data_len = len(data)
                data     = zlib.compress(data)

            data = VarInt.pack(data_len, ctx=self.ctx) + data

        data = VarInt.pack(len(data), ctx=self.ctx) + data

        if self.encryptor is not None:
            data = self.encryptor.update(data)

        self.transport.write(data)

    @abc.abstractmethod
    async def on_start():
        raise NotImplementedError

    @abc.abstractmethod
    async def start(self):
        # Has to be created here so it can get
        # the currently running loop
        self.read_queue = asyncio.Queue()

        await self.on_start()

    def run(self):
        try:
            asyncio.run(self.start())
        except KeyboardInterrupt:
            pass

    async def listen(self):
        while not self.closed:
            p = await self.read_packet()
            if p is None:
                return

            tasks = []
            for func, checker in self.packet_listeners.items():
                if checker(p):
                    if self.should_listen_sequentially:
                        tasks.append(func(p))
                    else:
                        asyncio.create_task(func(p))

            if self.should_listen_sequentially:
                await asyncio.gather(*tasks)
